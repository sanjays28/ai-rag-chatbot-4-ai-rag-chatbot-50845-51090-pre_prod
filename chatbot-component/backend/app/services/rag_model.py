"""RAG model service for handling model initialization and query processing."""
from typing import List, Dict, Optional, Tuple, Generator
import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from sentence_transformers import SentenceTransformer
from threading import Thread
from ..errors import RAGModelError
from ..config import Config
from ..monitoring import get_monitor, GenerationStats, EmbeddingStats, RetrievalStats

class RAGModel:
    """Service for handling RAG model operations."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize RAG model service.
        
        Args:
            model_name: Optional name of the model to use. If not provided,
                      uses the default from configuration.
        """
        self.model_name = model_name or Config.MODEL_NAME
        self.config = Config.MODEL_CONFIG
        self._initialized = False
        self._documents = []
        self._embeddings = None
        self._index = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """
        Initialize the RAG model with required configurations.
        
        Raises:
            RAGModelError: If there's an error initializing the model
        """
        try:
            # Initialize sentence transformer model for embeddings
            self._embedding_model = SentenceTransformer(self.config['embedding_model'])
            
            # Initialize FAISS index for similarity search
            self._index = faiss.IndexFlatL2(self._embedding_model.get_sentence_embedding_dimension())
            
            # Initialize LLM and tokenizer
            self._llm_tokenizer = AutoTokenizer.from_pretrained(self.config['llm_model'])
            self._llm = AutoModelForCausalLM.from_pretrained(
                self.config['llm_model'],
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            self._initialized = True
        except Exception as e:
            raise RAGModelError(f"Error initializing RAG model: {str(e)}")
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with specified size and overlap.
        
        Args:
            text: Text to be chunked
            
        Returns:
            List of text chunks
        """
        chunk_size = self.config['chunk_size']
        chunk_overlap = self.config['chunk_overlap']
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - chunk_overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks
    
    def _get_relevant_chunks(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Retrieve the most relevant chunks for a given query.
        
        Args:
            query: Query text
            top_k: Number of chunks to retrieve (defaults to config value)
            
        Returns:
            List of tuples containing (chunk_text, similarity_score)
        """
        monitor = get_monitor()
        monitor.start_operation("context_retrieval")
        
        try:
            if not self._embeddings or len(self._documents) == 0:
                return []
                
            k = top_k or self.config['top_k']
            query_embedding = self._embedding_model.encode([query])[0].reshape(1, -1)
            
            # Search for similar chunks
            distances, indices = self._index.search(query_embedding.astype(np.float32), k)
            
            results = []
            total_similarity = 0.0
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self._documents):
                    results.append((self._documents[idx], float(dist)))
                    total_similarity += float(dist)
            
            # Record retrieval statistics
            if results:
                avg_similarity = total_similarity / len(results)
                monitor.record_retrieval_stats(RetrievalStats(
                    retrieval_time=monitor.end_operation(),
                    num_chunks_retrieved=len(results),
                    avg_similarity_score=avg_similarity,
                    context_window_size=sum(len(chunk.split()) for chunk, _ in results)
                ))
            
            return results
            
        except Exception as e:
            monitor.end_operation()
            raise e
    
    def _generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for the query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            numpy.ndarray: Query embedding vector
            
        Raises:
            RAGModelError: If there's an error generating the embedding
        """
        try:
            return self._embedding_model.encode([query])[0]
        except Exception as e:
            raise RAGModelError(f"Error generating query embedding: {str(e)}")
    
    def _select_context_window(self, relevant_chunks: List[Tuple[str, float]], 
                             max_tokens: Optional[int] = None) -> str:
        """
        Select and combine relevant chunks into a context window.
        
        Args:
            relevant_chunks: List of (chunk_text, similarity_score) tuples
            max_tokens: Maximum number of tokens in the context window
            
        Returns:
            str: Combined context window text
        """
        max_tokens = max_tokens or self.config.get('max_context_tokens', 2048)
        context_chunks = []
        current_tokens = 0
        
        # Sort chunks by similarity score (ascending distances)
        sorted_chunks = sorted(relevant_chunks, key=lambda x: x[1])
        
        for chunk, _ in sorted_chunks:
            # Approximate token count by words (can be replaced with actual tokenizer)
            chunk_tokens = len(chunk.split())
            if current_tokens + chunk_tokens > max_tokens:
                break
                
            context_chunks.append(chunk)
            current_tokens += chunk_tokens
            
        return " ".join(context_chunks)
    
    def _format_prompt(self, query: str, context_window: str, chat_history: List[Dict] = None) -> str:
        """
        Format the prompt for the LLM using the query, context, and chat history.
        
        Args:
            query: The user's query
            context_window: Retrieved context from documents
            chat_history: Optional list of previous interactions
            
        Returns:
            str: Formatted prompt for the LLM
        """
        # Format chat history if available
        history_str = ""
        if chat_history:
            for interaction in chat_history[-3:]:  # Use last 3 interactions for context
                history_str += f"Human: {interaction['user']}\nAssistant: {interaction['bot']}\n"
        
        # Create the prompt with context and query
        prompt = f"""You are a helpful AI assistant. Use the following context to answer the question. 
If you cannot find the answer in the context, say so.

Context:
{context_window}

Chat History:
{history_str}
Human: {query}
Assistant: """
        
        return prompt
    
    def _generate_response_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Generate a streaming response using the LLM.
        
        Args:
            prompt: The formatted prompt for the LLM
            
        Yields:
            str: Generated text chunks
            
        Raises:
            RAGModelError: If there's an error generating the response
        """
        monitor = get_monitor()
        monitor.start_operation("response_generation")
        start_time = time.time()
        total_tokens = 0
        prompt_tokens = len(self._llm_tokenizer.encode(prompt))
        
        try:
            # Create a streamer for token-wise generation
            streamer = TextIteratorStreamer(self._llm_tokenizer)
            
            # Tokenize the prompt
            inputs = self._llm_tokenizer(prompt, return_tensors="pt").to(self._llm.device)
            
            # Generate in a separate thread to enable streaming
            generation_kwargs = {
                "input_ids": inputs.input_ids,
                "streamer": streamer,
                "max_new_tokens": self.config.get('max_new_tokens', 512),
                "temperature": self.config.get('temperature', 0.7),
                "top_k": self.config.get('top_k', 50),
                "top_p": self.config.get('top_p', 0.95),
                "repetition_penalty": self.config.get('repetition_penalty', 1.1),
                "do_sample": self.config.get('do_sample', True),
            }
            
            thread = Thread(target=self._llm.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Yield generated text chunks
            response_text = ""
            for text in streamer:
                response_text += text
                total_tokens += 1
                yield text
            
            # Record generation statistics
            generation_time = time.time() - start_time
            monitor.record_generation_stats(GenerationStats(
                total_time=generation_time,
                tokens_generated=total_tokens,
                tokens_per_second=total_tokens / generation_time if generation_time > 0 else 0,
                prompt_tokens=prompt_tokens,
                total_tokens=prompt_tokens + total_tokens
            ))
            
            # Record resource usage
            monitor.record_resource_usage()
                
        except Exception as e:
            monitor.end_operation()
            raise RAGModelError(f"Error generating response stream: {str(e)}")
    
    def process_query(self, query: str, context: List[Dict] = None) -> Generator[str, None, None]:
        """
        Process a query using the RAG model and generate a streaming response.
        
        Args:
            query: The user's query string
            context: Optional list of previous interactions for context
            
        Yields:
            str: Generated response chunks
            
        Raises:
            RAGModelError: If there's an error processing the query
        """
        try:
            if not self._initialized:
                raise RAGModelError("RAG model not initialized")
            
            if not query.strip():
                raise RAGModelError("Empty query provided")
            
            if not self._embeddings or len(self._documents) == 0:
                raise RAGModelError("No context documents available")
            
            # Get relevant chunks based on similarity search
            relevant_chunks = self._get_relevant_chunks(query)
            if not relevant_chunks:
                raise RAGModelError("No relevant context found for the query")
            
            # Select context window from relevant chunks
            context_window = self._select_context_window(relevant_chunks)
            
            # Format prompt with context and history
            prompt = self._format_prompt(query, context_window, context)
            
            # Generate streaming response
            for response_chunk in self._generate_response_stream(prompt):
                yield response_chunk
            
        except RAGModelError:
            raise
        except Exception as e:
            raise RAGModelError(f"Error processing query: {str(e)}")
    
    def update_context(self, documents: List[str]) -> None:
        """
        Update the model's context with new documents.
        
        Args:
            documents: List of document texts to add to the context
            
        Raises:
            RAGModelError: If there's an error updating the context
        """
        monitor = get_monitor()
        monitor.start_operation("embedding_generation")
        start_time = time.time()
        
        try:
            if not self._initialized:
                raise RAGModelError("RAG model not initialized")
            
            # Process each document into chunks
            all_chunks = []
            for doc in documents:
                chunks = self._chunk_text(doc)
                all_chunks.extend(chunks)
            
            if not all_chunks:
                return
            
            # Generate embeddings for all chunks
            embeddings = self._embedding_model.encode(all_chunks)
            
            # Record embedding statistics
            processing_time = time.time() - start_time
            monitor.record_embedding_stats(EmbeddingStats(
                processing_time=processing_time,
                num_chunks=len(all_chunks),
                avg_chunk_size=sum(len(chunk.split()) for chunk in all_chunks) / len(all_chunks),
                total_embeddings=len(embeddings)
            ))
            
            # Update FAISS index
            if self._embeddings is None:
                self._embeddings = embeddings
                self._documents = all_chunks
                self._index.add(embeddings.astype(np.float32))
            else:
                # Concatenate new embeddings with existing ones
                self._embeddings = np.vstack([self._embeddings, embeddings])
                self._documents.extend(all_chunks)
                self._index.add(embeddings.astype(np.float32))
            
            # Record resource usage after embedding generation
            monitor.record_resource_usage()
                
        except Exception as e:
            monitor.end_operation()
            raise RAGModelError(f"Error updating context: {str(e)}")
