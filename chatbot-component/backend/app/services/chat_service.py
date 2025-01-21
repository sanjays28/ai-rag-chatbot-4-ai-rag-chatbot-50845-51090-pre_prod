"""Chat service for handling chat interactions and RAG model integration."""
from typing import List, Dict, Optional, Generator
from ..errors import RAGModelError
from .rag_model import RAGModel

class ChatService:
    """Service for handling chat interactions and RAG model integration."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize chat service.
        
        Args:
            model_name: Optional name of the model to use
        """
        self._chat_history: List[Dict] = []
        self._rag_model = RAGModel(model_name)
    
    def generate_response(self, message: str) -> Generator[str, None, None]:
        """
        Generate a streaming response using the RAG model.
        
        Args:
            message: The user's input message
            
        Yields:
            str: Generated response chunks
            
        Raises:
            RAGModelError: If there's an error generating the response
        """
        try:
            # Initialize response storage
            full_response = []
            
            # Process the query using RAG model with chat history context
            for response_chunk in self._rag_model.process_query(
                query=message,
                context=self._chat_history
            ):
                full_response.append(response_chunk)
                yield response_chunk
            
            # Store the interaction in chat history after complete generation
            self._chat_history.append({
                'user': message,
                'bot': ''.join(full_response)
            })
        except Exception as e:
            raise RAGModelError(f"Error generating response: {str(e)}")
    
    def get_chat_history(self) -> List[Dict]:
        """
        Get the chat history for the current session.
        
        Returns:
            List[Dict]: List of chat interactions
        """
        return self._chat_history
    
    def clear_chat_history(self) -> None:
        """Clear the chat history for the current session."""
        self._chat_history.clear()
