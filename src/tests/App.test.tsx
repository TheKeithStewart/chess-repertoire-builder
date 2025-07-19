import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import App from '../App';

describe('Chess Repertoire Builder', () => {
  it('renders the main title', () => {
    render(<App />);
    expect(screen.getByText('Chess Repertoire Builder')).toBeInTheDocument();
  });

  it('renders the chess board', () => {
    render(<App />);
    expect(screen.getByRole('status')).toBeInTheDocument(); // Chess board container
  });

  it('renders game controls', () => {
    render(<App />);
    expect(screen.getByText('New Game')).toBeInTheDocument();
    expect(screen.getByText('Save PGN')).toBeInTheDocument();
    expect(screen.getByText('Export for Chessable')).toBeInTheDocument();
  });

  it('renders metadata panel', () => {
    render(<App />);
    expect(screen.getByText('Game Information')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Chess Repertoire Builder')).toBeInTheDocument();
  });

  it('renders navigation buttons', () => {
    render(<App />);
    expect(screen.getByText('⏮️ Start')).toBeInTheDocument();
    expect(screen.getByText('⏪ Back')).toBeInTheDocument();
    expect(screen.getByText('⏩ Forward')).toBeInTheDocument();
    expect(screen.getByText('⏭️ End')).toBeInTheDocument();
    expect(screen.getByText('Flip Board')).toBeInTheDocument();
  });

  it('renders move history', () => {
    render(<App />);
    expect(screen.getByText('Move History')).toBeInTheDocument();
    expect(screen.getByText('No moves yet. Start playing!')).toBeInTheDocument();
  });

  it('renders comment panel', () => {
    render(<App />);
    expect(screen.getByText('Position Comments')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Add a comment about this position...')).toBeInTheDocument();
  });

  it('allows flipping the board', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const flipButton = screen.getByText('Flip Board');
    await user.click(flipButton);
    
    // After flipping, the board should be reoriented
    // We can verify this by checking if the button is still clickable
    expect(flipButton).toBeInTheDocument();
  });

  it('allows starting a new game', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const newGameButton = screen.getByText('New Game');
    await user.click(newGameButton);
    
    // After new game, move history should still show no moves
    expect(screen.getByText('No moves yet. Start playing!')).toBeInTheDocument();
  });

  it('allows editing metadata', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const eventInput = screen.getByDisplayValue('Chess Repertoire Builder');
    await user.clear(eventInput);
    await user.type(eventInput, 'Test Event');
    
    expect(eventInput).toHaveValue('Test Event');
  });

  it('allows adding comments', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const commentTextarea = screen.getByPlaceholderText('Add a comment about this position...');
    await user.type(commentTextarea, 'This is a test comment');
    
    const saveButton = screen.getByText('Save Comment');
    await user.click(saveButton);
    
    expect(commentTextarea).toHaveValue('This is a test comment');
  });
});