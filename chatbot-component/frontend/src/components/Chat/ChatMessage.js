import React from 'react';
import PropTypes from 'prop-types';
import './ChatMessage.css';

const ChatMessage = ({ message }) => {
  const { text, sender, timestamp, type } = message;
  const formattedTime = new Date(timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });

  const messageClass = type === 'error' ? 'error-message' : `${sender}-message`;

  return (
    <div 
      className={`chat-message ${messageClass}`}
      data-testid={type === 'error' ? 'error-message' : `${sender}-message`}
    >
      <div className="message-content">
        <p>{text}</p>
        <span className="timestamp">{formattedTime}</span>
      </div>
    </div>
  );
};

ChatMessage.propTypes = {
  message: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    text: PropTypes.string.isRequired,
    sender: PropTypes.oneOf(['user', 'bot']).isRequired,
    timestamp: PropTypes.string.isRequired,
    type: PropTypes.string
  }).isRequired
};

export default ChatMessage;