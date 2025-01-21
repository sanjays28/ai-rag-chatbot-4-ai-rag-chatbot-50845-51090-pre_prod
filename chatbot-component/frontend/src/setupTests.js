// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import { render } from '@testing-library/react';

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = jest.fn();

// Mock IntersectionObserver
class MockIntersectionObserver {
  constructor(callback) {
    this.callback = callback;
  }

  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

window.IntersectionObserver = MockIntersectionObserver;

// Custom render function with providers if needed
const customRender = (ui, options = {}) => {
  return render(ui, {
    // wrap provider(s) here if required
    wrapper: ({ children }) => children,
    ...options,
  });
};

// re-export everything
export * from '@testing-library/react';

// override render method
export { customRender as render };
