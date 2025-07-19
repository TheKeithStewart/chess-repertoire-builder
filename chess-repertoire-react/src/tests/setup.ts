import '@testing-library/jest-dom';

// Mock ResizeObserver for react-chessboard
declare const global: any;
global.ResizeObserver = class MockResizeObserver {
  constructor(_callback: any) {}
  observe() {}
  unobserve() {}
  disconnect() {}
};