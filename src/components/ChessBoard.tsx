import React, { useState, useCallback, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess, type Square } from 'chess.js';

// Expose game instance for testing
declare global {
  interface Window {
    chessBoardGame?: Chess;
  }
}

interface ChessBoardProps {
  game: Chess;
  onMove: (move: string) => void;
  boardOrientation?: 'white' | 'black';
}

const ChessBoard: React.FC<ChessBoardProps> = ({ 
  game, 
  onMove, 
  boardOrientation = 'white' 
}) => {
  const [selectedSquare, setSelectedSquare] = useState<Square | null>(null);
  const [legalMoves, setLegalMoves] = useState<Square[]>([]);

  // Expose game to window for e2e testing
  useEffect(() => {
    window.chessBoardGame = game;
    
    return () => {
      delete window.chessBoardGame;
    };
  }, [game]);

  // Handle piece drop for drag and drop
  const handlePieceDrop = useCallback((sourceSquare: Square, targetSquare: Square) => {
    try {
      // Create a new Chess instance to attempt the move without affecting the original game
      const newGame = new Chess(game.fen());
      
      const moveObj = newGame.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q' // Default to queen promotion
      });
      
      if (moveObj) {
        // If move is valid, notify the parent component
        onMove(sourceSquare + targetSquare);
        setSelectedSquare(null);
        setLegalMoves([]);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Invalid move:', error);
      return false;
    }
  }, [game, onMove]);

  // Handle square click for click-based moves
  const handleSquareClick = useCallback((square: Square) => {
    if (selectedSquare) {
      // If a square is already selected, attempt to move to the clicked square
      const moveResult = handlePieceDrop(selectedSquare, square);
      
      if (!moveResult) {
        // If move failed, check if the new square has a piece of the correct color
        const piece = game.get(square);
        if (piece && piece.color === game.turn()) {
          // Select the new piece
          setSelectedSquare(square);
          const moves = game.moves({ square, verbose: true });
          setLegalMoves(moves.map(move => move.to as Square));
        } else {
          // Clear selection if clicking on empty square or opponent's piece
          setSelectedSquare(null);
          setLegalMoves([]);
        }
      }
    } else {
      // If no square is selected, check if the clicked square has a piece
      const piece = game.get(square);
      if (piece && piece.color === game.turn()) {
        // Select the piece and show legal moves
        setSelectedSquare(square);
        const moves = game.moves({ square, verbose: true });
        setLegalMoves(moves.map(move => move.to as Square));
      }
    }
  }, [selectedSquare, game, handlePieceDrop]);

  // Create custom square styles for highlighting
  const customSquareStyles = React.useMemo(() => {
    const styles: { [square: string]: React.CSSProperties } = {};
    
    if (selectedSquare) {
      styles[selectedSquare] = {
        backgroundColor: 'rgba(255, 255, 0, 0.4)'
      };
    }
    
    legalMoves.forEach(square => {
      styles[square] = {
        backgroundColor: 'rgba(0, 255, 0, 0.4)'
      };
    });
    
    return styles;
  }, [selectedSquare, legalMoves]);

  return (
    <div className="chess-board-container">
      <Chessboard
        options={{
          position: game.fen(),
          onSquareClick: (params: { square: string }) => {
            handleSquareClick(params.square as Square);
          },
          onPieceDrop: (params: { sourceSquare: string, targetSquare: string | null }) => {
            if (!params.targetSquare) return false;
            return handlePieceDrop(params.sourceSquare as Square, params.targetSquare as Square);
          },
          squareStyles: customSquareStyles,
          boardOrientation: boardOrientation,
          animationDurationInMs: 200,
          showNotation: true,
          boardStyle: { 
            borderRadius: '8px',
            boxShadow: '0 5px 15px rgba(0, 0, 0, 0.2)'
          },
          darkSquareStyle: { backgroundColor: '#779952' },
          lightSquareStyle: { backgroundColor: '#edeed1' }
        }}
      />
    </div>
  );
};

export default ChessBoard;