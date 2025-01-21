import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MessageInput from '../components/Chat/MessageInput';

describe('MessageInput', () => {
  const mockOnSend = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<MessageInput />);
    expect(screen.getByTestId('message-input')).toBeInTheDocument();
  });

  it('updates input value on change', () => {
    render(<MessageInput onSend={mockOnSend} />);
    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(input.value).toBe('Test message');
  });

  it('calls onSend when Enter is pressed with non-empty message', () => {
    render(<MessageInput onSend={mockOnSend} />);
    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    expect(mockOnSend).toHaveBeenCalledWith('Test message');
    expect(input.value).toBe('');
  });

  it('does not call onSend when Enter is pressed with empty message', () => {
    render(<MessageInput onSend={mockOnSend} />);
    const input = screen.getByTestId('message-input');
    fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('disables input when disabled prop is true', () => {
    render(<MessageInput disabled={true} />);
    expect(screen.getByTestId('message-input')).toBeDisabled();
  });

  it('shows loading indicator when isLoading is true', () => {
    render(<MessageInput isLoading={true} />);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    expect(screen.getByText('Sending...')).toBeInTheDocument();
  });

  it('does not show loading indicator when isLoading is false', () => {
    render(<MessageInput isLoading={false} />);
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  it('does not call onSend when Enter is pressed and disabled is true', () => {
    render(<MessageInput onSend={mockOnSend} disabled={true} />);
    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    expect(mockOnSend).not.toHaveBeenCalled();
  });
});