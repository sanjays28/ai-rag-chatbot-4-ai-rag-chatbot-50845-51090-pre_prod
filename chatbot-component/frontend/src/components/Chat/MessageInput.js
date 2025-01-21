import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './MessageInput.css';

const MessageInput = ({ onSend, disabled, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && message.trim() && !disabled) {
      onSend(message);
      setMessage('');
    }
  };

  const handleChange = (e) => {
    setMessage(e.target.value);
  };

  return (
    <div className="message-input-container">
      <input
        type="text"
        value={message}
        onChange={handleChange}
        onKeyPress={handleKeyPress}
        placeholder="Type your message..."
        disabled={disabled}
        data-testid="message-input"
        className="message-input"
      />
      {isLoading && (
        <div className="loading-indicator" data-testid="loading-indicator">
          <span>Sending...</span>
        </div>
      )}
    </div>
  );
};

MessageInput.propTypes = {
  onSend: PropTypes.func,
  disabled: PropTypes.bool,
  isLoading: PropTypes.bool
};

MessageInput.defaultProps = {
  onSend: () => {},
  disabled: false,
  isLoading: false
};

export default MessageInput;