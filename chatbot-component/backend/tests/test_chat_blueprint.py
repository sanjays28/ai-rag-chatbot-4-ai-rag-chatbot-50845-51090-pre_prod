"""Tests for chat blueprint API endpoints."""
import json
import pytest
from unittest.mock import patch
from app.errors import APIError

def test_chat_endpoint_success(client, mock_rag_response):
    """Test successful chat message processing."""
    with patch('app.services.chat_service.ChatService.generate_response') as mock_generate:
        mock_generate.return_value = iter([mock_rag_response])
        
        response = client.post('/chat', 
                             data=json.dumps({'message': 'test message'}),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['response'] == mock_rag_response

def test_chat_endpoint_missing_message(client):
    """Test chat endpoint with missing message."""
    response = client.post('/chat',
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Message is required' in data['error']

def test_chat_endpoint_empty_message(client):
    """Test chat endpoint with empty message."""
    response = client.post('/chat',
                          data=json.dumps({'message': ''}),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'

def test_chat_endpoint_error_handling(client):
    """Test chat endpoint error handling."""
    with patch('app.services.chat_service.ChatService.generate_response') as mock_generate:
        mock_generate.side_effect = APIError('Test error', status_code=500)
        
        response = client.post('/chat',
                             data=json.dumps({'message': 'test message'}),
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Test error' in data['error']

def test_get_chat_history_success(client):
    """Test successful retrieval of chat history."""
    with patch('app.services.chat_service.ChatService.get_chat_history') as mock_history:
        mock_history.return_value = [
            {'user': 'test message', 'bot': 'test response'}
        ]
        
        response = client.get('/chat/history')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['history']) == 1
        assert data['history'][0]['user'] == 'test message'
        assert data['history'][0]['bot'] == 'test response'

def test_get_chat_history_error(client):
    """Test chat history retrieval error handling."""
    with patch('app.services.chat_service.ChatService.get_chat_history') as mock_history:
        mock_history.side_effect = APIError('Test error', status_code=500)
        
        response = client.get('/chat/history')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Test error' in data['error']

def test_clear_chat_success(client):
    """Test successful chat history clearing."""
    response = client.post('/chat/clear')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['message'] == 'Chat history cleared'

def test_clear_chat_error(client):
    """Test chat history clearing error handling."""
    with patch('app.services.chat_service.ChatService.clear_chat_history') as mock_clear:
        mock_clear.side_effect = APIError('Test error', status_code=500)
        
        response = client.post('/chat/clear')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Test error' in data['error']