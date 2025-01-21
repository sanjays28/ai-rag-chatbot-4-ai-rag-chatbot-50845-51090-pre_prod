"""Error handling module for the Flask application."""
from flask import jsonify

class APIError(Exception):
    """Base class for API errors."""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert error to dictionary format."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv

class PDFProcessingError(APIError):
    """Raised when there's an error processing a PDF file."""
    pass

class RAGModelError(APIError):
    """Raised when there's an error with the RAG model."""
    pass

class InvalidFileError(APIError):
    """Raised when an invalid file is uploaded."""
    pass

def init_app(app):
    """Initialize error handlers for the application."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return jsonify({
            'status': 'error',
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            'status': 'error',
            'message': 'An internal error occurred'
        }), 500