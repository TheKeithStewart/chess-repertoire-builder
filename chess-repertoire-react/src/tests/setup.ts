import '@testing-library/jest-dom';

// Mock ResizeObserver for react-chessboard
global.ResizeObserver = class MockResizeObserver {
  constructor(callback: any) {}
  observe() {}
  unobserve() {}
  disconnect() {}
};