import React, { useState, useCallback } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess, type Square } from 'chess.js';

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

  const handleSquareClick = useCallback((args: { piece: any; square: string }) => {
    const { square } = args;
    const squareAsSquare = square as Square;
    if (selectedSquare) {
      // Try to make move
      const move = selectedSquare + square;
      const moveObj = game.move({
        from: selectedSquare,
        to: squareAsSquare,
        promotion: 'q' // Default to queen promotion
      });
      
      if (moveObj) {
        onMove(move);
        setSelectedSquare(null);
        setLegalMoves([]);
      } else {
        // Select new square if it has a piece
        const piece = game.get(squareAsSquare);
        if (piece && piece.color === game.turn()) {
          setSelectedSquare(squareAsSquare);
          const moves = game.moves({ square: squareAsSquare, verbose: true });
          setLegalMoves(moves.map(move => move.to));
        } else {
          setSelectedSquare(null);
          setLegalMoves([]);
        }
      }
    } else {
      // Select square if it has a piece of the correct color
      const piece = game.get(squareAsSquare);
      if (piece && piece.color === game.turn()) {
        setSelectedSquare(squareAsSquare);
        const moves = game.moves({ square: squareAsSquare, verbose: true });
        setLegalMoves(moves.map(move => move.to));
      }
    }
  }, [selectedSquare, game, onMove]);

  const handlePieceDrop = useCallback((args: { piece: any; sourceSquare: string; targetSquare: string | null }) => {
    const { sourceSquare, targetSquare } = args;
    if (!targetSquare) return false;
    
    try {
      const moveObj = game.move({
        from: sourceSquare as Square,
        to: targetSquare as Square,
        promotion: 'q' // Default to queen promotion
      });
      
      if (moveObj) {
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
          onPieceDrop: handlePieceDrop,
          onSquareClick: handleSquareClick,
          boardOrientation: boardOrientation,
          squareStyles: customSquareStyles,
          showNotation: true,
          boardStyle: { borderRadius: '8px' }
        }}
      />
    </div>
  );
};

export default ChessBoard;