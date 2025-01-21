"""Shared test fixtures for backend tests."""
import os
import tempfile
import pytest
from app import create_app
from app.services.chat_service import ChatService
from app.services.pdf_processor import PDFProcessor
from app.services.rag_model import RAGModel

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    # Create a temporary directory for uploads
    upload_dir = tempfile.mkdtemp()
    
    app = create_app({
        'TESTING': True,
        'UPLOAD_FOLDER': upload_dir,
        'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,  # 5MB
        'ALLOWED_EXTENSIONS': {'pdf'}
    })
    
    yield app
    
    # Cleanup temporary directory
    for root, dirs, files in os.walk(upload_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(upload_dir)

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def chat_service():
    """Create a ChatService instance for testing."""
    return ChatService()

@pytest.fixture
def pdf_processor():
    """Create a PDFProcessor instance for testing."""
    return PDFProcessor()

@pytest.fixture
def rag_model():
    """Create a RAGModel instance for testing."""
    return RAGModel()

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n70 700 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000254 00000 n\n0000000332 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n427\n%%EOF"
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_rag_response():
    """Mock RAG model response for testing."""
    return "This is a test response from the RAG model."