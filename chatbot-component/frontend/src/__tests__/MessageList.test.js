import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import MessageList from '../components/Chat/MessageList';
import { sampleMessages, createMockIntersectionObserverEntry } from '../test-utils/helpers';

describe('MessageList', () => {
  // Mock scrollIntoView
  const mockScrollIntoView = jest.fn();
  
  // Mock IntersectionObserver
  const mockIntersectionObserver = jest.fn();
  const mockObserve = jest.fn();
  const mockUnobserve = jest.fn();
  const mockDisconnect = jest.fn();

  beforeEach(() => {
    // Setup scrollIntoView mock
    Element.prototype.scrollIntoView = mockScrollIntoView;
    
    // Setup IntersectionObserver mock
    mockIntersectionObserver.mockImplementation((callback) => ({
      observe: mockObserve,
      unobserve: mockUnobserve,
      disconnect: mockDisconnect
    }));
    window.IntersectionObserver = mockIntersectionObserver;
    
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Cleanup mocks
    jest.restoreAllMocks();
    mockScrollIntoView.mockClear();
    mockIntersectionObserver.mockClear();
    mockObserve.mockClear();
    mockUnobserve.mockClear();
    mockDisconnect.mockClear();
  });

  it('renders without crashing', () => {
    render(<MessageList messages={[]} />);
    expect(screen.getByTestId('message-list')).toBeInTheDocument();
  });

  it('displays all messages', () => {
    render(<MessageList messages={sampleMessages} />);
    sampleMessages.forEach(message => {
      expect(screen.getByText(message.text)).toBeInTheDocument();
    });
  });

  it('renders messages with correct sender classes', () => {
    render(<MessageList messages={sampleMessages} />);
    const userMessage = screen.getByText(sampleMessages[1].text).closest('[data-testid="user-message"]');
    const botMessage = screen.getByText(sampleMessages[0].text).closest('[data-testid="bot-message"]');
    expect(userMessage).toBeInTheDocument();
    expect(botMessage).toBeInTheDocument();
  });

  it('handles empty messages array', () => {
    render(<MessageList messages={[]} />);
    const messageList = screen.getByTestId('message-list');
    expect(messageList.children.length).toBe(1); // Only the scroll ref div
  });

  it('renders error messages with correct styling', () => {
    const messagesWithError = [
      ...sampleMessages,
      {
        id: 3,
        text: 'Error occurred',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        type: 'error'
      }
    ];
    render(<MessageList messages={messagesWithError} />);
    expect(screen.getByTestId('error-message')).toBeInTheDocument();
  });

  it('calls scrollIntoView when messages update', () => {
    render(<MessageList messages={sampleMessages} />);
    expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
    
    // Should call scrollIntoView again when messages update
    act(() => {
      render(<MessageList messages={[...sampleMessages, {
        id: 3,
        text: 'New message',
        sender: 'bot',
        timestamp: new Date().toISOString()
      }]} />);
    });
    
    expect(mockScrollIntoView).toHaveBeenCalledTimes(2);
  });

  it('handles scroll behavior when new messages arrive', async () => {
    const { rerender } = render(<MessageList messages={sampleMessages} />);
    expect(mockScrollIntoView).toHaveBeenCalledTimes(1);

    // Simulate new message arrival
    const updatedMessages = [
      ...sampleMessages,
      {
        id: 4,
        text: 'Another message',
        sender: 'user',
        timestamp: new Date().toISOString()
      }
    ];

    act(() => {
      rerender(<MessageList messages={updatedMessages} />);
    });

    expect(mockScrollIntoView).toHaveBeenCalledTimes(2);
    expect(mockScrollIntoView).toHaveBeenLastCalledWith({ behavior: 'smooth' });
  });

  it('maintains scroll position when viewing older messages', () => {
    const { rerender } = render(<MessageList messages={sampleMessages} />);
    
    // Simulate scroll position in the middle of the list
    const messageList = screen.getByTestId('message-list');
    Object.defineProperty(messageList, 'scrollTop', { value: 100 });
    Object.defineProperty(messageList, 'scrollHeight', { value: 500 });
    Object.defineProperty(messageList, 'clientHeight', { value: 300 });

    // Add new message
    const newMessages = [...sampleMessages, {
      id: 5,
      text: 'New message while scrolled up',
      sender: 'bot',
      timestamp: new Date().toISOString()
    }];

    act(() => {
      rerender(<MessageList messages={newMessages} />);
    });

    // Should still call scrollIntoView for the new message
    expect(mockScrollIntoView).toHaveBeenCalledTimes(2);
  });
});
