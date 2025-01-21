import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './PDFUpload.css';

// PUBLIC_INTERFACE
const PDFUpload = ({ onUploadComplete }) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    
    if (!file) {
      setError('Please select a file');
      return;
    }

    if (file.type !== 'application/pdf') {
      setError('Only PDF files are allowed');
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload-pdf', {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        },
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setUploadProgress(100);
      onUploadComplete && onUploadComplete(data);
    } catch (err) {
      setError('Failed to upload file: ' + err.message);
    } finally {
      setIsUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  return (
    <div className="pdf-upload-container">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${error ? 'error' : ''}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the PDF file here...</p>
        ) : (
          <p>Drag and drop a PDF file here, or click to select</p>
        )}
      </div>

      {isUploading && (
        <div className="progress-container">
          <div className="progress-bar" role="progressbar" aria-valuenow={uploadProgress} aria-valuemin="0" aria-valuemax="100">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <span className="progress-text">{uploadProgress}%</span>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default PDFUpload;
