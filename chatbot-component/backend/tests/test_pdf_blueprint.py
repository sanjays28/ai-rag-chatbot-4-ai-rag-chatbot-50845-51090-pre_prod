"""Tests for PDF blueprint API endpoints."""
import os
import json
import pytest
from unittest.mock import patch
from werkzeug.datastructures import FileStorage
from app.errors import APIError, InvalidFileError

def test_upload_pdf_success(client, sample_pdf):
    """Test successful PDF file upload."""
    with open(sample_pdf, 'rb') as pdf:
        data = {
            'file': (pdf, 'test.pdf', 'application/pdf')
        }
        response = client.post('/pdf/upload',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'File uploaded and processed successfully'
        assert data['filename'] == 'test.pdf'
        assert 'text_length' in data
        assert 'file_size' in data

def test_upload_pdf_no_file(client):
    """Test PDF upload with no file."""
    response = client.post('/pdf/upload')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No file provided' in data['error']

def test_upload_pdf_empty_filename(client):
    """Test PDF upload with empty filename."""
    data = {
        'file': (b'', '', 'application/pdf')
    }
    response = client.post('/pdf/upload',
                          data=data,
                          content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No file selected' in data['error']

def test_upload_pdf_invalid_type(client):
    """Test PDF upload with invalid file type."""
    data = {
        'file': (b'test content', 'test.txt', 'text/plain')
    }
    response = client.post('/pdf/upload',
                          data=data,
                          content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid file type' in data['error']

def test_upload_pdf_file_too_large(client, sample_pdf):
    """Test PDF upload with file exceeding size limit."""
    with patch('app.blueprints.pdf.validate_file_size') as mock_validate:
        mock_validate.side_effect = InvalidFileError(
            'File size exceeds maximum limit',
            status_code=413
        )
        
        with open(sample_pdf, 'rb') as pdf:
            data = {
                'file': (pdf, 'test.pdf', 'application/pdf')
            }
            response = client.post('/pdf/upload',
                                 data=data,
                                 content_type='multipart/form-data')
            
            assert response.status_code == 413
            data = json.loads(response.data)
            assert 'error' in data
            assert 'File size exceeds maximum limit' in data['error']

def test_upload_pdf_processing_error(client, sample_pdf):
    """Test PDF upload with processing error."""
    with patch('app.services.pdf_processor.PDFProcessor.process_pdf') as mock_process:
        mock_process.side_effect = APIError('Processing error', status_code=500)
        
        with open(sample_pdf, 'rb') as pdf:
            data = {
                'file': (pdf, 'test.pdf', 'application/pdf')
            }
            response = client.post('/pdf/upload',
                                 data=data,
                                 content_type='multipart/form-data')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Processing error' in data['error']

def test_list_pdfs_success(client):
    """Test successful PDF file listing."""
    with patch('app.services.pdf_processor.PDFProcessor.list_processed_files') as mock_list:
        mock_list.return_value = ['test1.pdf', 'test2.pdf']
        
        response = client.get('/pdf/list')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['files']) == 2
        assert 'test1.pdf' in data['files']
        assert 'test2.pdf' in data['files']

def test_list_pdfs_error(client):
    """Test PDF file listing error handling."""
    with patch('app.services.pdf_processor.PDFProcessor.list_processed_files') as mock_list:
        mock_list.side_effect = APIError('Listing error', status_code=500)
        
        response = client.get('/pdf/list')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Listing error' in data['error']

def test_delete_pdf_success(client):
    """Test successful PDF file deletion."""
    response = client.delete('/pdf/test.pdf')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['message'] == 'File test.pdf deleted successfully'

def test_delete_pdf_error(client):
    """Test PDF file deletion error handling."""
    with patch('app.services.pdf_processor.PDFProcessor.delete_file') as mock_delete:
        mock_delete.side_effect = APIError('Deletion error', status_code=500)
        
        response = client.delete('/pdf/test.pdf')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Deletion error' in data['error']