"""Tests for RAGModel."""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.services.rag_model import RAGModel
from app.errors import RAGModelError

@pytest.fixture
def mock_embedding_model():
    """Mock embedding model for testing."""
    with patch('sentence_transformers.SentenceTransformer') as mock:
        model = MagicMock()
        model.get_sentence_embedding_dimension.return_value = 384
        model.encode.return_value = np.random.rand(1, 384)
        mock.return_value = model
        yield mock

@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock:
        model = MagicMock()
        mock.return_value = model
        yield mock

@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer for testing."""
    with patch('transformers.AutoTokenizer.from_pretrained') as mock:
        tokenizer = MagicMock()
        tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock.return_value = tokenizer
        yield mock

def test_rag_model_initialization(mock_embedding_model, mock_llm, mock_tokenizer):
    """Test RAGModel initialization."""
    model = RAGModel()
    assert model._initialized
    assert model._documents == []
    assert model._embeddings is None
    assert model._index is not None

def test_chunk_text():
    """Test text chunking functionality."""
    model = RAGModel()
    text = "This is a test document. It has multiple sentences. " * 5
    chunks = model._chunk_text(text)
    
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk.split()) <= model.config['chunk_size'] for chunk in chunks)

def test_get_relevant_chunks_empty(mock_embedding_model):
    """Test getting relevant chunks with no documents."""
    model = RAGModel()
    chunks = model._get_relevant_chunks("test query")
    assert chunks == []

def test_get_relevant_chunks_with_documents(mock_embedding_model):
    """Test getting relevant chunks with documents."""
    model = RAGModel()
    documents = ["This is document one.", "This is document two."]
    model.update_context(documents)
    
    chunks = model._get_relevant_chunks("test query")
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(chunk, tuple) for chunk in chunks)
    assert all(isinstance(chunk[0], str) and isinstance(chunk[1], float) 
              for chunk in chunks)

def test_generate_query_embedding(mock_embedding_model):
    """Test query embedding generation."""
    model = RAGModel()
    embedding = model._generate_query_embedding("test query")
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[-1] == 384  # Mock embedding dimension

def test_select_context_window():
    """Test context window selection."""
    model = RAGModel()
    chunks = [
        ("chunk1", 0.1),
        ("chunk2", 0.2),
        ("chunk3", 0.3)
    ]
    context = model._select_context_window(chunks)
    assert isinstance(context, str)
    assert "chunk1" in context
    assert "chunk2" in context
    assert "chunk3" in context

def test_format_prompt():
    """Test prompt formatting."""
    model = RAGModel()
    query = "test query"
    context = "test context"
    history = [
        {"user": "previous query", "bot": "previous response"}
    ]
    
    prompt = model._format_prompt(query, context, history)
    assert isinstance(prompt, str)
    assert query in prompt
    assert context in prompt
    assert "previous query" in prompt
    assert "previous response" in prompt

@pytest.mark.asyncio
async def test_generate_response_stream(mock_embedding_model, mock_llm, mock_tokenizer):
    """Test response stream generation."""
    model = RAGModel()
    prompt = "test prompt"
    
    # Mock the streamer
    with patch('transformers.TextIteratorStreamer') as mock_streamer:
        streamer = MagicMock()
        streamer.__iter__.return_value = iter(["Hello", " ", "World"])
        mock_streamer.return_value = streamer
        
        response = list(model._generate_response_stream(prompt))
        assert len(response) == 3
        assert "".join(response) == "Hello World"

def test_process_query_no_context(mock_embedding_model):
    """Test query processing with no context documents."""
    model = RAGModel()
    with pytest.raises(RAGModelError) as exc:
        list(model.process_query("test query"))
    assert "No context documents available" in str(exc.value)

def test_process_query_empty_query(mock_embedding_model):
    """Test processing empty query."""
    model = RAGModel()
    with pytest.raises(RAGModelError) as exc:
        list(model.process_query(""))
    assert "Empty query provided" in str(exc.value)

def test_update_context_success(mock_embedding_model):
    """Test successful context update."""
    model = RAGModel()
    documents = ["This is a test document.", "This is another test document."]
    model.update_context(documents)
    
    assert len(model._documents) > 0
    assert model._embeddings is not None
    assert model._index is not None

def test_update_context_empty_documents(mock_embedding_model):
    """Test context update with empty documents."""
    model = RAGModel()
    model.update_context([])
    
    assert len(model._documents) == 0
    assert model._embeddings is None

def test_update_context_error(mock_embedding_model):
    """Test context update error handling."""
    model = RAGModel()
    mock_embedding_model.return_value.encode.side_effect = Exception("Test error")
    
    with pytest.raises(RAGModelError) as exc:
        model.update_context(["test document"])
    assert "Error updating context" in str(exc.value)