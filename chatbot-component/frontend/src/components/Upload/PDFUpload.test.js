import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PDFUpload from './PDFUpload';

// Mock the fetch function globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('PDFUpload Component', () => {
  beforeEach(() => {
    // Clear mock before each test
    mockFetch.mockClear();
  });
  it('renders upload area', () => {
    render(<PDFUpload />);
    expect(screen.getByText(/Drag and drop a PDF file here/i)).toBeInTheDocument();
  });

  it('shows error for non-PDF files', async () => {
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    render(<PDFUpload />);

    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [file],
      },
    });

    await waitFor(() => {
      expect(screen.getByText(/Only PDF files are allowed/i)).toBeInTheDocument();
    });
  });

  it('shows drag active state when dragging file over dropzone', () => {
    render(<PDFUpload />);
    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    
    fireEvent.dragEnter(dropzone);
    expect(screen.getByText(/Drop the PDF file here/i)).toBeInTheDocument();
    
    fireEvent.dragLeave(dropzone);
    expect(screen.getByText(/Drag and drop a PDF file here/i)).toBeInTheDocument();
  });

  it('displays upload progress during file upload', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    mockFetch.mockImplementationOnce(() => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
    });

    render(<PDFUpload />);
    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  it('handles successful upload with progress indication', async () => {
    const mockOnUploadComplete = jest.fn();
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    
    mockFetch.mockImplementationOnce(() => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
    });

    render(<PDFUpload onUploadComplete={mockOnUploadComplete} />);
    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(mockOnUploadComplete).toHaveBeenCalledWith({ success: true });
    });
  });

  it('handles upload failure with server error', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    
    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      })
    );

    render(<PDFUpload />);
    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to upload file/i)).toBeInTheDocument();
    });
  });

  it('handles file selection through click', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    mockFetch.mockImplementationOnce(() => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
    });

    render(<PDFUpload />);
    const input = screen.getByRole('button');
    
    // Simulate file selection
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    
    fireEvent.change(input, {
      target: { files: dataTransfer.files }
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  it('handles no file selected', async () => {
    render(<PDFUpload />);
    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [] }
    });

    await waitFor(() => {
      expect(screen.getByText(/Please select a file/i)).toBeInTheDocument();
    });
  });

  it('clears error state on successful file selection', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    mockFetch.mockImplementationOnce(() => {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
    });

    render(<PDFUpload />);
    const dropzone = screen.getByText(/Drag and drop a PDF file here/i);
    
    // First trigger an error
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [] }
    });

    await waitFor(() => {
      expect(screen.getByText(/Please select a file/i)).toBeInTheDocument();
    });

    // Then upload a valid file
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    await waitFor(() => {
      expect(screen.queryByText(/Please select a file/i)).not.toBeInTheDocument();
    });
  });
});
