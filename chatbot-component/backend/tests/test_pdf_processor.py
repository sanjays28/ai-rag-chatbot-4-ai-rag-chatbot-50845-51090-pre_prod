"""Tests for PDFProcessor."""
import os
import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_processor import PDFProcessor
from app.errors import PDFProcessingError

def test_process_pdf_success(pdf_processor, sample_pdf):
    """Test successful PDF processing."""
    text = pdf_processor.process_pdf(sample_pdf)
    assert text is not None
    assert isinstance(text, str)
    assert len(text) > 0
    assert 'Test PDF Content' in text

def test_process_pdf_invalid_file(pdf_processor):
    """Test processing invalid PDF file."""
    with pytest.raises(PDFProcessingError) as exc:
        pdf_processor.process_pdf('nonexistent.pdf')
    assert 'Error processing PDF' in str(exc.value)

def test_process_pdf_with_progress_callback(pdf_processor, sample_pdf):
    """Test PDF processing with progress callback."""
    progress_values = []
    
    def progress_callback(value):
        progress_values.append(value)
    
    text = pdf_processor.process_pdf(sample_pdf, progress_callback)
    
    assert text is not None
    assert len(progress_values) > 0
    assert min(progress_values) >= 0
    assert max(progress_values) <= 100

def test_process_pdf_empty_file(pdf_processor, tmp_path):
    """Test processing empty PDF file."""
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"%PDF-1.4\n")
    
    with pytest.raises(PDFProcessingError) as exc:
        pdf_processor.process_pdf(str(empty_pdf))
    assert 'No text could be extracted' in str(exc.value)

def test_list_processed_files_success(pdf_processor, app):
    """Test successful listing of processed files."""
    # Create some test files
    upload_folder = app.config['UPLOAD_FOLDER']
    test_files = ['test1.pdf', 'test2.pdf', 'test3.txt']
    
    for filename in test_files:
        path = os.path.join(upload_folder, filename)
        with open(path, 'w') as f:
            f.write('test content')
    
    files = pdf_processor.list_processed_files()
    
    assert len(files) == 2  # Should only list PDF files
    assert 'test1.pdf' in files
    assert 'test2.pdf' in files
    assert 'test3.txt' not in files
    
    # Cleanup
    for filename in test_files:
        os.remove(os.path.join(upload_folder, filename))

def test_list_processed_files_empty(pdf_processor, app):
    """Test listing processed files from empty directory."""
    files = pdf_processor.list_processed_files()
    assert isinstance(files, list)
    assert len(files) == 0

def test_list_processed_files_error(pdf_processor):
    """Test error handling in list_processed_files."""
    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = OSError('Test error')
        
        with pytest.raises(PDFProcessingError) as exc:
            pdf_processor.list_processed_files()
        assert 'Error listing files' in str(exc.value)

def test_delete_file_success(pdf_processor, app):
    """Test successful file deletion."""
    # Create test file
    test_file = os.path.join(app.config['UPLOAD_FOLDER'], 'test.pdf')
    with open(test_file, 'w') as f:
        f.write('test content')
    
    pdf_processor.delete_file('test.pdf')
    assert not os.path.exists(test_file)

def test_delete_file_not_found(pdf_processor):
    """Test deleting non-existent file."""
    with pytest.raises(PDFProcessingError) as exc:
        pdf_processor.delete_file('nonexistent.pdf')
    assert 'File nonexistent.pdf not found' in str(exc.value)

def test_delete_file_error(pdf_processor, app):
    """Test error handling in delete_file."""
    # Create test file
    test_file = os.path.join(app.config['UPLOAD_FOLDER'], 'test.pdf')
    with open(test_file, 'w') as f:
        f.write('test content')
    
    with patch('os.remove') as mock_remove:
        mock_remove.side_effect = OSError('Test error')
        
        with pytest.raises(PDFProcessingError) as exc:
            pdf_processor.delete_file('test.pdf')
        assert 'Error deleting file' in str(exc.value)
    
    # Cleanup
    os.remove(test_file)