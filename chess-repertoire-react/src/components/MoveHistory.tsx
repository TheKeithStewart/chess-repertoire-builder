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
  // Process moves into a proper PGN-style display with move pairs and variations
  const renderMoveList = (movesToRender = moves, isVariation = false, depth = 0) => {
    if (movesToRender.length === 0) {
      return isVariation ? null : <p className="no-moves">No moves yet. Start playing!</p>;
    }

    // Group moves by move number for main line display
    const movesByNumber: { [key: number]: { white?: Move, black?: Move } } = {};
    
    // Process moves for display
    const movesToProcess = isVariation ? movesToRender : movesToRender.filter(move => move.originalIndex !== -1);
    
    for (let i = 0; i < movesToProcess.length; i++) {
      const move = movesToProcess[i];
      const moveNumber = Math.ceil((i + 1) / 2);
      
      if (!movesByNumber[moveNumber]) {
        movesByNumber[moveNumber] = {};
      }
      
      if (i % 2 === 0) {
        movesByNumber[moveNumber].white = move;
      } else {
        movesByNumber[moveNumber].black = move;
      }
    }

    const result = [];
    const moveNumbers = Object.keys(movesByNumber).map(Number).sort((a, b) => a - b);
    
    for (const moveNumber of moveNumbers) {
      const pair = movesByNumber[moveNumber];
      
      // Main line move pair
      result.push(
        <div key={`move-pair-${moveNumber}-${depth}`} className={`move-pair ${isVariation ? 'variation-move-pair' : 'main-line-move-pair'}`}>
          <span className="move-number-label">{moveNumber}.</span>
          
          {/* White's move */}
          {pair.white && (
            <>
              {renderMoveItem(pair.white, pair.white.originalIndex ?? -1)}
              {/* Render variations after White's move */}
              {pair.white.variation && pair.white.variation.length > 0 && (
                <div className="variation-container" style={{ marginLeft: `${(depth + 1) * 1.5}rem` }}>
                  <div className="variation-label">Variation after {pair.white.san}:</div>
                  <div className="variation-content">
                    {renderMoveList(pair.white.variation, true, depth + 1)}
                  </div>
                </div>
              )}
            </>
          )}
          
          {/* Black's move */}
          {pair.black && (
            <>
              {!pair.white && <span className="move-ellipsis">...</span>}
              {renderMoveItem(pair.black, pair.black.originalIndex ?? -1)}
              {/* Render variations after Black's move */}
              {pair.black.variation && pair.black.variation.length > 0 && (
                <div className="variation-container" style={{ marginLeft: `${(depth + 1) * 1.5}rem` }}>
                  <div className="variation-label">Variation after {pair.black.san}:</div>
                  <div className="variation-content">
                    {renderMoveList(pair.black.variation, true, depth + 1)}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      );
    }
    
    return result;
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
        {renderMoveList()}
      </div>
    </div>
  );
};

export default MoveHistory;
export type { Move };