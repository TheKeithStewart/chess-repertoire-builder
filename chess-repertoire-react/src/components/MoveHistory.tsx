import React from 'react';

interface Move {
  move: string;
  san: string;
  comment?: string;
  moveNumber?: number;
  isWhite?: boolean;
  variation?: Move[]; // For storing variations
  variationTitle?: string; // For naming variations (e.g., "Queen's Gambit Accepted")
  originalIndex?: number; // For tracking the original index in the array
}

interface MoveHistoryProps {
  moves: Move[];
  currentMoveIndex: number;
  onMoveClick: (index: number) => void;
}

const MoveHistory: React.FC<MoveHistoryProps> = ({
  moves,
  currentMoveIndex,
  onMoveClick
}) => {
  // Process moves into a tree-like display format
  const renderMoveSequence = (movesToRender = moves, depth = 0) => {
    if (movesToRender.length === 0) {
      return depth === 0 ? <p className="no-moves">No moves yet. Start playing!</p> : null;
    }

    const result = [];
    const mainLineMoves = movesToRender.filter(move => move.originalIndex !== -1);
    
    // Track the current position in the main line for variations
    let currentMainLineIndex = 0;
    
    // Process main line moves and their variations
    for (let i = 0; i < mainLineMoves.length; i++) {
      const move = mainLineMoves[i];
      const moveNumber = Math.ceil((i + 1) / 2);
      const isWhite = i % 2 === 0;
      
      // Add main line move
      if (isWhite) {
        // Start a new move pair
        result.push(
          <span key={`move-${i}-${depth}`} className="move-sequence">
            <span className="move-number-label">{moveNumber}.</span>
            {renderMoveItem(move, move.originalIndex ?? -1)}
            {/* Add a space after white's move */}
            {' '}
          </span>
        );
      } else {
        // Add black's move inline
        result.push(
          <span key={`move-${i}-${depth}`} className="move-sequence">
            {renderMoveItem(move, move.originalIndex ?? -1)}
            {i < mainLineMoves.length - 1 ? ' ' : ''}
          </span>
        );
      }
      
      // Check for variations after this move
      if (move.variation && move.variation.length > 0) {
        result.push(
          <div key={`variations-${i}-${depth}`} className="variation-block">
            {renderVariation(move.variation, move.san, depth + 1)}
          </div>
        );
      }
    }
    
    return <div className={`move-line ${depth === 0 ? 'main-line' : 'variation-line'}`}>{result}</div>;
  };

  // Render variations in tree format with |- prefix
  const renderVariation = (variation: Move[], parentMove: string, depth: number) => {
    if (!variation || variation.length === 0) return null;

    const variationMoves = [];
    
    for (let i = 0; i < variation.length; i++) {
      const move = variation[i];
      const moveNumber = Math.ceil((i + 1) / 2);
      const isWhite = i % 2 === 0;
      
      if (isWhite) {
        variationMoves.push(
          <span key={`var-move-${i}-${depth}`} className="move-sequence">
            <span className="move-number-label">{moveNumber}.</span>
            {renderMoveItem(move, move.originalIndex ?? -1)}
            {' '}
          </span>
        );
      } else {
        variationMoves.push(
          <span key={`var-move-${i}-${depth}`} className="move-sequence">
            {renderMoveItem(move, move.originalIndex ?? -1)}
            {i < variation.length - 1 ? ' ' : ''}
          </span>
        );
      }
    }

    return (
      <div 
        className="variation-line" 
        style={{ 
          marginLeft: `${depth * 1.5}rem`,
          borderLeft: `2px solid #3498db`,
          paddingLeft: '0.5rem',
          marginTop: '0.25rem',
          marginBottom: '0.25rem'
        }}
      >
        <span className="variation-prefix">|- </span>
        {variationMoves}
      </div>
    );
  };
  
  // Render an individual move item
  const renderMoveItem = (move: Move, index: number) => {
    const isCurrentMove = index >= 0 && index === currentMoveIndex;
    const colorClass = move.isWhite ? 'white-move' : 'black-move';
    const isVariationMove = index < 0; // Negative index indicates a variation move
    
    return (
      <span
        className={`move-item ${colorClass} ${isCurrentMove ? 'current-move' : ''}`}
        onClick={() => !isVariationMove && index >= 0 && onMoveClick(index)}
        title={move.comment || ''}
      >
        <span className="move-san">{move.san}</span>
        {move.comment && <span className="move-comment-indicator">💭</span>}
      </span>
    );
  };

  return (
    <div className="move-history">
      <h3>Move History</h3>
      <div className="move-list">
        {renderMoveSequence()}
      </div>
    </div>
  );
};

export default MoveHistory;
export type { Move };