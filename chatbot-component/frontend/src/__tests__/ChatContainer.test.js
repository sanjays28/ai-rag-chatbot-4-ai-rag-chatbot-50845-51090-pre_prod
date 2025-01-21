import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatContainer from '../components/Chat/ChatContainer';
import { sampleMessages, mockApiResponses } from '../test-utils/helpers';

describe('ChatContainer', () => {
  let mockConsoleError;
  
  beforeAll(() => {
    mockConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterAll(() => {
    mockConsoleError.mockRestore();
  });
  const mockOnSendMessage = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<ChatContainer />);
    expect(screen.getByTestId('chat-container')).toBeInTheDocument();
  });

  it('displays initial messages', () => {
    render(<ChatContainer initialMessages={sampleMessages} />);
    sampleMessages.forEach(message => {
      expect(screen.getByText(message.text)).toBeInTheDocument();
    });
  });

  it('handles sending a message successfully', async () => {
    mockOnSendMessage.mockResolvedValueOnce({ text: mockApiResponses.chatResponse.message });
    render(<ChatContainer onSendMessage={mockOnSendMessage} />);

    const input = screen.getByTestId('message-input');
    const testMessage = 'Test message';
    
    await act(async () => {
      fireEvent.change(input, { target: { value: testMessage } });
      fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    });

    expect(mockOnSendMessage).toHaveBeenCalledWith(testMessage);
    
    await waitFor(() => {
      const messages = screen.getAllByRole('listitem');
      expect(messages).toHaveLength(2); // User message and bot response
      expect(messages[1]).toHaveTextContent(mockApiResponses.chatResponse.message);
    });

    expect(input.value).toBe(''); // Input should be cleared after sending
  });

  it('handles error when sending message fails', async () => {
    const errorMessage = 'Network error occurred';
    mockOnSendMessage.mockRejectedValueOnce(new Error(errorMessage));
    render(<ChatContainer onSendMessage={mockOnSendMessage} />);

    const input = screen.getByTestId('message-input');
    const testMessage = 'Test message';
    
    await act(async () => {
      fireEvent.change(input, { target: { value: testMessage } });
      fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    });

    await waitFor(() => {
      const messages = screen.getAllByRole('listitem');
      expect(messages).toHaveLength(2); // User message and error message
      expect(messages[0]).toHaveTextContent(testMessage);
      expect(messages[1]).toHaveAttribute('data-type', 'error');
      expect(screen.getByTestId('error-message')).toHaveTextContent('Failed to send message');
    });

    expect(mockConsoleError).toHaveBeenCalled();
    expect(input).not.toBeDisabled(); // Input should be re-enabled after error
    expect(input.value).toBe(''); // Input should be cleared even after error
  });

  it('manages loading state and input state correctly while sending message', async () => {
    const delay = 100;
    mockOnSendMessage.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ text: 'Response' }), delay))
    );
    
    render(<ChatContainer onSendMessage={mockOnSendMessage} />);
    const input = screen.getByTestId('message-input');
    const testMessage = 'Test message';

    await act(async () => {
      fireEvent.change(input, { target: { value: testMessage } });
      fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    });

    // Verify loading state
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    expect(input).toBeDisabled();

    // Wait for response and verify states are reset
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
      expect(input).not.toBeDisabled();
      expect(input.value).toBe('');
    });

    // Verify message list updated correctly
    const messages = screen.getAllByRole('listitem');
    expect(messages).toHaveLength(2);
    expect(messages[0]).toHaveTextContent(testMessage);
    expect(messages[1]).toHaveTextContent('Response');
  });

  it('prevents sending empty messages', async () => {
    render(<ChatContainer onSendMessage={mockOnSendMessage} />);
    const input = screen.getByTestId('message-input');

    await act(async () => {
      fireEvent.change(input, { target: { value: '   ' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    });

    expect(mockOnSendMessage).not.toHaveBeenCalled();
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument();
  });

  it('maintains message order and timestamps', async () => {
    const messages = [
      { id: 1, text: 'First message', sender: 'user', timestamp: '2023-01-01T00:00:00.000Z' },
      { id: 2, text: 'Second message', sender: 'bot', timestamp: '2023-01-01T00:00:01.000Z' }
    ];
    
    render(<ChatContainer initialMessages={messages} />);
    
    const messageElements = screen.getAllByRole('listitem');
    expect(messageElements).toHaveLength(2);
    expect(messageElements[0]).toHaveTextContent('First message');
    expect(messageElements[1]).toHaveTextContent('Second message');
    
    // Verify timestamps are preserved
    messageElements.forEach((element, index) => {
      expect(element).toHaveAttribute('data-timestamp', messages[index].timestamp);
    });
  });
});
