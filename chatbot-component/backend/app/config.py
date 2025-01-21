"""Configuration settings for the Flask application."""
import os

class Config:
    """Base configuration class."""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # File upload and storage settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_FILE_AGE = 3600  # Maximum file age in seconds (1 hour)
    CLEANUP_INTERVAL = 300  # Cleanup interval in seconds (5 minutes)
    
    # RAG model settings
    MODEL_NAME = os.environ.get('MODEL_NAME', 'default-rag-model')
    MODEL_CONFIG = {
        # Embedding model settings
        'embedding_model': os.environ.get('EMBEDDING_MODEL', 'sentence-transformers/all-mpnet-base-v2'),
        'chunk_size': int(os.environ.get('CHUNK_SIZE', '512')),
        'chunk_overlap': int(os.environ.get('CHUNK_OVERLAP', '50')),
        
        # LLM settings
        'llm_model': os.environ.get('LLM_MODEL', 'meta-llama/Llama-2-7b-chat-hf'),
        'max_new_tokens': int(os.environ.get('MAX_NEW_TOKENS', '512')),
        'max_context_tokens': int(os.environ.get('MAX_CONTEXT_TOKENS', '2048')),
        'temperature': float(os.environ.get('TEMPERATURE', '0.7')),
        'top_k': int(os.environ.get('TOP_K', '3')),
        'top_p': float(os.environ.get('TOP_P', '0.95')),
        'repetition_penalty': float(os.environ.get('REPETITION_PENALTY', '1.1')),
        'do_sample': os.environ.get('DO_SAMPLE', 'True').lower() == 'true',
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application with the configuration."""
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    # Use temporary folder for uploads during testing
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_uploads')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, secret key should be set in environment
    SECRET_KEY = os.environ.get('SECRET_KEY')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
