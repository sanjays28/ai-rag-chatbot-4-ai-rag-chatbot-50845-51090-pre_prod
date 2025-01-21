import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatMessage from '../components/Chat/ChatMessage';
import { sampleMessages } from '../test-utils/helpers';

describe('ChatMessage', () => {
  // Mock Date.prototype.toLocaleTimeString to ensure consistent output
  const mockToLocaleTimeString = jest.spyOn(Date.prototype, 'toLocaleTimeString');
  const mockErrorMessage = {
    id: 3,
    text: 'An error occurred',
    sender: 'bot',
    timestamp: new Date().toISOString(),
    type: 'error'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    cleanup();
    // Mock toLocaleTimeString to return consistent output
    mockToLocaleTimeString.mockImplementation(function() {
      return new Date(this).toTimeString().slice(0, 5);
    });
  });

  afterEach(() => {
    cleanup();
    jest.resetAllMocks();
  });

  it('renders user message correctly', () => {
    const userMessage = sampleMessages[1]; // User message from sample data
    render(<ChatMessage message={userMessage} />);
    expect(screen.getByTestId('user-message')).toBeInTheDocument();
    expect(screen.getByText(userMessage.text)).toBeInTheDocument();
    
    const timestamp = new Date(userMessage.timestamp);
    const expectedTime = timestamp.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    expect(screen.getByText(expectedTime)).toBeInTheDocument();
  });

  it('renders bot message correctly', () => {
    const botMessage = sampleMessages[0]; // Bot message from sample data
    render(<ChatMessage message={botMessage} />);
    expect(screen.getByTestId('bot-message')).toBeInTheDocument();
    expect(screen.getByText(botMessage.text)).toBeInTheDocument();
    
    const timestamp = new Date(botMessage.timestamp);
    const expectedTime = timestamp.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    expect(screen.getByText(expectedTime)).toBeInTheDocument();
  });

  it('renders error message with correct styling', () => {
    render(<ChatMessage message={mockErrorMessage} />);
    expect(screen.getByTestId('error-message')).toBeInTheDocument();
    expect(screen.getByText(mockErrorMessage.text)).toBeInTheDocument();
    
    const timestamp = new Date(mockErrorMessage.timestamp);
    const expectedTime = timestamp.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    expect(screen.getByText(expectedTime)).toBeInTheDocument();
  });

  it('formats timestamp correctly for different timezones', () => {
    const testCases = [
      { input: '2023-01-01T15:30:00.000Z', expected: '15:30' },
      { input: '2023-01-01T00:00:00.000Z', expected: '00:00' },
      { input: '2023-01-01T23:59:59.000Z', expected: '23:59' }
    ];

    testCases.forEach(({ input, expected }) => {
      const message = {
        ...sampleMessages[0],
        timestamp: input
      };
      render(<ChatMessage message={message} />);
      expect(screen.getByText(expected)).toBeInTheDocument();
      cleanup();
    });
  });

  it('handles invalid timestamp gracefully', () => {
    const message = {
      ...sampleMessages[0],
      timestamp: 'invalid-date'
    };
    render(<ChatMessage message={message} />);
    expect(screen.getByTestId('bot-message')).toBeInTheDocument();
    expect(screen.getByText(message.text)).toBeInTheDocument();
  });

  it('applies correct CSS classes based on message type', () => {
    const testCases = [
      { message: sampleMessages[1], expectedClasses: ['chat-message', 'user-message'], testId: 'user-message' },
      { message: sampleMessages[0], expectedClasses: ['chat-message', 'bot-message'], testId: 'bot-message' },
      { message: mockErrorMessage, expectedClasses: ['chat-message', 'error-message'], testId: 'error-message' }
    ];

    testCases.forEach(({ message, expectedClasses, testId }) => {
      render(<ChatMessage message={message} />);
      const messageElement = screen.getByTestId(testId);
      expectedClasses.forEach(className => {
        expect(messageElement).toHaveClass(className);
      });
      cleanup();
    });
  });

  it('renders message content in correct structure', () => {
    const message = sampleMessages[0];
    render(<ChatMessage message={message} />);
    
    const contentDiv = screen.getByText(message.text).closest('.message-content');
    expect(contentDiv).toBeInTheDocument();
    expect(contentDiv).toHaveClass('message-content');
    expect(contentDiv.querySelector('.timestamp')).toBeInTheDocument();
  });
});
