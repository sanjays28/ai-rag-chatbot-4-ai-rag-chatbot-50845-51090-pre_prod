// Common test helpers and fixtures

// Sample message data
export const sampleMessages = [
  {
    id: 1,
    text: 'Hello, how can I help you?',
    sender: 'bot',
    timestamp: new Date().toISOString(),
  },
  {
    id: 2,
    text: 'I have a question about the document.',
    sender: 'user',
    timestamp: new Date().toISOString(),
  },
];

// Mock file data
export const mockPdfFile = new File(['dummy pdf content'], 'test.pdf', {
  type: 'application/pdf',
});

// Mock API responses
export const mockApiResponses = {
  chatResponse: {
    message: 'This is a response from the chatbot.',
    timestamp: new Date().toISOString(),
  },
  uploadResponse: {
    success: true,
    message: 'File uploaded successfully',
  },
};

// Event helpers
export const createMockIntersectionObserverEntry = (isIntersecting = true) => ({
  isIntersecting,
  target: document.createElement('div'),
  boundingClientRect: {},
  intersectionRatio: isIntersecting ? 1 : 0,
  intersectionRect: {},
  rootBounds: {},
  time: Date.now(),
});

// Mock function helpers
export const createMockFunction = () => {
  return jest.fn().mockImplementation((...args) => {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });
  });
};