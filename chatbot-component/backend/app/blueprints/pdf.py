"""PDF blueprint for handling PDF file operations."""
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..services.pdf_processor import PDFProcessor
from ..errors import APIError, InvalidFileError

bp = Blueprint('pdf', __name__)
pdf_processor = PDFProcessor()

def validate_file_size(file):
    """
    Validate file size against MAX_CONTENT_LENGTH.
    
    Args:
        file: FileStorage object from request
        
    Returns:
        bool: True if file size is within limits
        
    Raises:
        InvalidFileError: If file size exceeds limit
    """
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > current_app.config['MAX_CONTENT_LENGTH']:
        max_size_mb = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        raise InvalidFileError(
            f'File size exceeds maximum limit of {max_size_mb}MB',
            status_code=413
        )
    return True

def allowed_file(filename):
    """
    Check if the file extension is allowed.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        bool: True if file extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# PUBLIC_INTERFACE
@bp.route('/pdf/upload', methods=['POST'])
def upload_pdf():
    """
    Handle PDF file upload and processing.
    
    Expects a file in the request with key 'file'.
    Validates file type, size, and processes the PDF for text extraction.
    
    Returns:
        JSON response with upload status and processed file details
        
    Raises:
        InvalidFileError: For file validation failures
        APIError: For processing errors
    """
    # Check if file was provided
    if 'file' not in request.files:
        raise InvalidFileError('No file provided', status_code=400)
    
    file = request.files['file']
    
    # Validate file selection
    if file.filename == '':
        raise InvalidFileError('No file selected', status_code=400)
    
    # Validate file type
    if not allowed_file(file.filename):
        raise InvalidFileError('Invalid file type. Only PDF files are allowed.', status_code=400)
    
    try:
        # Validate file size
        validate_file_size(file)
        
        # Secure filename and save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            raise InvalidFileError(
                'A file with this name already exists. Please rename the file.',
                status_code=409
            )
        
        file.save(filepath)
        current_app.logger.info(f'File saved successfully: {filename}')
        
        # Process the PDF file
        text_content = pdf_processor.process_pdf(filepath)
        current_app.logger.info(f'File processed successfully: {filename}')
        
        return jsonify({
            'status': 'success',
            'message': 'File uploaded and processed successfully',
            'filename': filename,
            'text_length': len(text_content),
            'file_size': os.path.getsize(filepath)
        })
    except InvalidFileError:
        # Re-raise validation errors
        raise
    except Exception as e:
        current_app.logger.error(f'Error processing file {file.filename}: {str(e)}')
        # Clean up file if saved but processing failed
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as cleanup_error:
                current_app.logger.error(f'Error cleaning up file {filepath}: {str(cleanup_error)}')
        raise APIError(f'Error processing file: {str(e)}', status_code=500)

@bp.route('/pdf/list', methods=['GET'])
def list_pdfs():
    """List all processed PDF files."""
    try:
        files = pdf_processor.list_processed_files()
        return jsonify({
            'status': 'success',
            'files': files
        })
    except Exception as e:
        raise APIError(str(e), status_code=500)

@bp.route('/pdf/<filename>', methods=['DELETE'])
def delete_pdf(filename):
    """Delete a processed PDF file."""
    try:
        pdf_processor.delete_file(filename)
        return jsonify({
            'status': 'success',
            'message': f'File {filename} deleted successfully'
        })
    except Exception as e:
        raise APIError(str(e), status_code=500)
