import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatContainer.css';

const ChatContainer = ({ initialMessages, onSendMessage }) => {
  const [messages, setMessages] = useState(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSendMessage = useCallback(async (text) => {
    if (!text.trim()) return;

    const newMessage = {
      id: Date.now(),
      text,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await onSendMessage(text);
      const botMessage = {
        id: Date.now() + 1,
        text: response.text,
        sender: 'bot',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError('Failed to send message');
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Failed to send message',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        type: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [onSendMessage]);

  return (
    <div className="chat-container" data-testid="chat-container">
      <MessageList messages={messages} />
      <MessageInput 
        onSend={handleSendMessage}
        disabled={isLoading}
        isLoading={isLoading}
      />
      {error && (
        <div className="error-message" data-testid="error-message">
          {error}
        </div>
      )}
    </div>
  );
};

ChatContainer.propTypes = {
  initialMessages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      text: PropTypes.string.isRequired,
      sender: PropTypes.oneOf(['user', 'bot']).isRequired,
      timestamp: PropTypes.string.isRequired,
      type: PropTypes.string
    })
  ),
  onSendMessage: PropTypes.func
};

ChatContainer.defaultProps = {
  initialMessages: [],
  onSendMessage: async () => ({ text: 'Default response' })
};

export default ChatContainer;