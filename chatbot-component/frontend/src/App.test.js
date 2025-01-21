import { render, screen } from '@testing-library/react';
import App from './App';

test('renders chat container', () => {
  render(<App />);
  const chatContainer = screen.getByTestId('chat-container');
  expect(chatContainer).toBeInTheDocument();
});
