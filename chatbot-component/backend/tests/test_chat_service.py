"""Tests for ChatService."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.chat_service import ChatService
from app.errors import RAGModelError

def test_chat_service_initialization():
    """Test ChatService initialization."""
    service = ChatService()
    assert service._chat_history == []
    assert service._rag_model is not None

def test_generate_response_success(chat_service, mock_rag_response):
    """Test successful response generation."""
    with patch('app.services.rag_model.RAGModel.process_query') as mock_process:
        mock_process.return_value = iter([mock_rag_response])
        
        response = list(chat_service.generate_response('test message'))
        
        assert len(response) == 1
        assert response[0] == mock_rag_response
        assert len(chat_service._chat_history) == 1
        assert chat_service._chat_history[0]['user'] == 'test message'
        assert chat_service._chat_history[0]['bot'] == mock_rag_response

def test_generate_response_error(chat_service):
    """Test response generation error handling."""
    with patch('app.services.rag_model.RAGModel.process_query') as mock_process:
        mock_process.side_effect = RAGModelError('Test error')
        
        with pytest.raises(RAGModelError) as exc:
            list(chat_service.generate_response('test message'))
        
        assert 'Test error' in str(exc.value)
        assert len(chat_service._chat_history) == 0

def test_get_chat_history_empty(chat_service):
    """Test getting empty chat history."""
    history = chat_service.get_chat_history()
    assert history == []

def test_get_chat_history_with_messages(chat_service, mock_rag_response):
    """Test getting chat history with messages."""
    # Add some messages to history
    with patch('app.services.rag_model.RAGModel.process_query') as mock_process:
        mock_process.return_value = iter([mock_rag_response])
        list(chat_service.generate_response('test message 1'))
        list(chat_service.generate_response('test message 2'))
    
    history = chat_service.get_chat_history()
    assert len(history) == 2
    assert history[0]['user'] == 'test message 1'
    assert history[1]['user'] == 'test message 2'

def test_clear_chat_history(chat_service, mock_rag_response):
    """Test clearing chat history."""
    # Add some messages to history
    with patch('app.services.rag_model.RAGModel.process_query') as mock_process:
        mock_process.return_value = iter([mock_rag_response])
        list(chat_service.generate_response('test message'))
    
    assert len(chat_service.get_chat_history()) == 1
    
    chat_service.clear_chat_history()
    assert len(chat_service.get_chat_history()) == 0

def test_generate_response_streaming(chat_service):
    """Test streaming response generation."""
    response_chunks = ['Hello', ' ', 'World', '!']
    
    with patch('app.services.rag_model.RAGModel.process_query') as mock_process:
        mock_process.return_value = iter(response_chunks)
        
        generated = list(chat_service.generate_response('test message'))
        
        assert generated == response_chunks
        assert len(chat_service._chat_history) == 1
        assert chat_service._chat_history[0]['bot'] == 'Hello World!'

def test_generate_response_empty_message(chat_service):
    """Test response generation with empty message."""
    with patch('app.services.rag_model.RAGModel.process_query') as mock_process:
        mock_process.return_value = iter(['Empty response'])
        
        response = list(chat_service.generate_response(''))
        
        assert len(response) == 1
        assert response[0] == 'Empty response'
        assert len(chat_service._chat_history) == 1