import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import MoveHistory from '../components/MoveHistory';
import type { Move } from '../components/MoveHistory';

describe('MoveHistory Component', () => {
  // Basic rendering test
  it('renders "No moves yet" when no moves are provided', () => {
    render(<MoveHistory moves={[]} currentMoveIndex={-1} onMoveClick={() => {}} />);
    expect(screen.getByText('No moves yet. Start playing!')).toBeInTheDocument();
  });

  // Test rendering of basic moves
  it('renders a simple move sequence correctly', () => {
    const moves: Move[] = [
      { move: 'e2e4', san: 'e4', isWhite: true, originalIndex: 0 },
      { move: 'e7e5', san: 'e5', isWhite: false, originalIndex: 1 },
      { move: 'g1f3', san: 'Nf3', isWhite: true, originalIndex: 2 }
    ];

    render(<MoveHistory moves={moves} currentMoveIndex={-1} onMoveClick={() => {}} />);
    
    expect(screen.getByText('1.')).toBeInTheDocument();
    expect(screen.getByText('e4')).toBeInTheDocument();
    expect(screen.getByText('e5')).toBeInTheDocument();
    expect(screen.getByText('2.')).toBeInTheDocument();
    expect(screen.getByText('Nf3')).toBeInTheDocument();
  });

  // Test rendering with variations
  it('renders moves with variations correctly', () => {
    const moves: Move[] = [
      { move: 'd2d4', san: 'd4', isWhite: true, originalIndex: 0 },
      { 
        move: 'd7d5', 
        san: 'd5', 
        isWhite: false,
        originalIndex: 1,
        variation: [
          { move: 'c7c5', san: 'c5', isWhite: false, originalIndex: -1 },
          { move: 'd4c5', san: 'dxc5', isWhite: true, originalIndex: -1 }
        ]
      },
      { move: 'c2c4', san: 'c4', isWhite: true, originalIndex: 2 },
      { move: 'd5c4', san: 'dxc4', isWhite: false, originalIndex: 3 }
    ];

    render(<MoveHistory moves={moves} currentMoveIndex={-1} onMoveClick={() => {}} />);
    
    // Check main line moves
    expect(screen.getAllByText('1.').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('d4')).toBeInTheDocument();
    expect(screen.getByText('d5')).toBeInTheDocument();
    expect(screen.getByText('2.')).toBeInTheDocument();
    expect(screen.getByText('c4')).toBeInTheDocument();
    expect(screen.getByText('dxc4')).toBeInTheDocument();
    
    // Check that variation moves are present
    expect(screen.getByText('c5')).toBeInTheDocument();
    expect(screen.getByText('dxc5')).toBeInTheDocument();
    
    // Check for variation prefix (tree-like display)
    expect(screen.getByText('|-')).toBeInTheDocument();
  });

  // Test click handler
  it('calls onMoveClick with the correct index when a move is clicked', async () => {
    const user = userEvent.setup();
    const handleMoveClick = vi.fn();
    
    const moves: Move[] = [
      { move: 'e2e4', san: 'e4', isWhite: true, originalIndex: 0 },
      { move: 'e7e5', san: 'e5', isWhite: false, originalIndex: 1 }
    ];

    render(
      <MoveHistory 
        moves={moves} 
        currentMoveIndex={-1} 
        onMoveClick={handleMoveClick} 
      />
    );

    // Click on the first move
    const firstMove = screen.getByText('e4');
    await user.click(firstMove);
    
    // Check if onMoveClick was called with the correct index
    expect(handleMoveClick).toHaveBeenCalledWith(0);
  });

  // Test current move highlighting
  it('highlights the current move correctly', () => {
    const moves: Move[] = [
      { move: 'e2e4', san: 'e4', isWhite: true, originalIndex: 0 },
      { move: 'e7e5', san: 'e5', isWhite: false, originalIndex: 1 }
    ];

    render(
      <MoveHistory 
        moves={moves} 
        currentMoveIndex={1} 
        onMoveClick={() => {}} 
      />
    );

    // The second move should have the 'current-move' class
    const e5Move = screen.getByText('e5').closest('.move-item');
    expect(e5Move).toHaveClass('current-move');
    
    // The first move should NOT have the 'current-move' class
    const e4Move = screen.getByText('e4').closest('.move-item');
    expect(e4Move).not.toHaveClass('current-move');
  });
});
