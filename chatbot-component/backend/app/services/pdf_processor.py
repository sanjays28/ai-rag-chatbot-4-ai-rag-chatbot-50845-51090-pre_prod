"""PDF processor service for handling PDF file operations."""
import os
from typing import List, Optional
from flask import current_app
from PyPDF2 import PdfReader
from ..errors import PDFProcessingError

class PDFProcessor:
    """Service for processing PDF files and extracting text."""
    
    def process_pdf(self, filepath: str, progress_callback: Optional[callable] = None) -> str:
        """
        Process a PDF file and extract its text content.
        
        Args:
            filepath: Path to the PDF file
            progress_callback: Optional callback function to track progress
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFProcessingError: If there's an error processing the PDF
        """
        try:
            with open(filepath, 'rb') as file:
                # Create PDF reader object
                reader = PdfReader(file)
                total_pages = len(reader.pages)
                extracted_text = []
                
                # Extract text from each page
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            extracted_text.append(text)
                        
                        # Update progress if callback provided
                        if progress_callback:
                            progress = (i + 1) / total_pages * 100
                            progress_callback(progress)
                            
                    except Exception as e:
                        current_app.logger.warning(f"Error extracting text from page {i}: {str(e)}")
                        continue
                
                if not extracted_text:
                    raise PDFProcessingError("No text could be extracted from the PDF")
                
                return "\n\n".join(extracted_text)
        except Exception as e:
            raise PDFProcessingError(f"Error processing PDF: {str(e)}")
    
    def list_processed_files(self) -> List[str]:
        """
        List all processed PDF files.
        
        Returns:
            List[str]: List of processed PDF filenames
        """
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            files = [f for f in os.listdir(upload_folder) 
                    if f.lower().endswith('.pdf')]
            return files
        except Exception as e:
            raise PDFProcessingError(f"Error listing files: {str(e)}")
    
    def delete_file(self, filename: str) -> None:
        """
        Delete a processed PDF file.
        
        Args:
            filename: Name of the file to delete
            
        Raises:
            PDFProcessingError: If there's an error deleting the file
        """
        try:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            else:
                raise PDFProcessingError(f"File {filename} not found")
        except Exception as e:
            raise PDFProcessingError(f"Error deleting file: {str(e)}")
