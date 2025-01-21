"""Chat blueprint for handling chat-related routes."""
from flask import Blueprint, request, jsonify
from ..services.chat_service import ChatService
from ..errors import APIError

bp = Blueprint('chat', __name__)
chat_service = ChatService()

@bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and generate responses."""
    data = request.get_json()
    if not data or 'message' not in data:
        raise APIError('Message is required', status_code=400)
    
    try:
        response = chat_service.generate_response(data['message'])
        return jsonify({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        raise APIError(str(e), status_code=500)

@bp.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history for the current session."""
    try:
        history = chat_service.get_chat_history()
        return jsonify({
            'status': 'success',
            'history': history
        })
    except Exception as e:
        raise APIError(str(e), status_code=500)

@bp.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Clear the current chat session."""
    try:
        chat_service.clear_chat_history()
        return jsonify({
            'status': 'success',
            'message': 'Chat history cleared'
        })
    except Exception as e:
        raise APIError(str(e), status_code=500)