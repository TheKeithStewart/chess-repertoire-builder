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

    // Process all moves and ensure we have consistent isWhite values
    const normalizedMoves = movesToRender.map((move, index) => {
      // Use the explicitly provided isWhite if available, otherwise calculate based on index
      let isWhite = move.isWhite !== undefined ? move.isWhite : index % 2 === 0;
      
      return {
        ...move,
        isWhite,
        originalIndex: move.originalIndex !== undefined ? move.originalIndex : index
      };
    });

    // Group moves by main line and variations
    const mainLine: (Move & { originalIndex: number })[] = [];
    const variations: { startIndex: number; moves: (Move & { originalIndex: number })[]; title?: string }[] = [];
    
    // Extract variations from the moves
    normalizedMoves.forEach(move => {
      if (move.variation && move.variation.length > 0) {
        // Add this move to main line
        mainLine.push(move);
        
        // Store the variation with its starting index
        variations.push({
          startIndex: mainLine.length - 1,
          moves: move.variation.map((varMove, idx) => ({
            ...varMove,
            originalIndex: varMove.originalIndex !== undefined ? varMove.originalIndex : -1, // -1 indicates variation move
            isWhite: varMove.isWhite !== undefined ? varMove.isWhite : idx % 2 === (move.isWhite ? 0 : 1)
          })),
          title: move.variationTitle
        });
      } else {
        mainLine.push(move);
      }
    });
    
    // Build move groupings for the main line
    const movesByNumber: { [key: number]: { white?: Move & { originalIndex: number }, black?: Move & { originalIndex: number } } } = {};
    
    // Determine the correct move number for each half-move
    let currentMoveNumber = 1;
    
    for (let i = 0; i < mainLine.length; i++) {
      const move = mainLine[i];
      const isWhiteMove = move.isWhite;
      
      // Initialize the move number entry if it doesn't exist
      if (!movesByNumber[currentMoveNumber]) {
        movesByNumber[currentMoveNumber] = {};
      }
      
      // Add the move to the correct color slot
      if (isWhiteMove) {
        movesByNumber[currentMoveNumber].white = move;
        // Next move should be Black's
      } else {
        movesByNumber[currentMoveNumber].black = move;
        currentMoveNumber++; // Increment move number after Black's move
        // Next move should be White's
      }
    }

    // Create the move list with variations
    const moveGroups = Object.entries(movesByNumber).map(([moveNum, pair]) => {
      const moveNumber = parseInt(moveNum);
      
      return (
        <div key={`move-${moveNumber}-${depth}`} className={`move-group ${isVariation ? 'variation' : ''}`}>
          {/* Always show the move number */}
          <span className="move-number-label">{moveNumber}.</span>
          
          {/* Show White's move if available */}
          {pair.white && renderMoveItem(pair.white, pair.white.originalIndex)}
          
          {/* Show Black's move with proper ellipsis if needed */}
          {pair.black && (
            <>
              {!pair.white && (
                <span className="move-ellipsis">...</span>
              )}
              {renderMoveItem(pair.black, pair.black.originalIndex)}
            </>
          )}
          
          {/* Add variation title if available */}
          {!isVariation && pair.black?.variationTitle && (
            <span className="variation-title">{pair.black.variationTitle}</span>
          )}
          {!isVariation && pair.white?.variationTitle && (
            <span className="variation-title">{pair.white.variationTitle}</span>
          )}
        </div>
      );
    });

    // Add variations to the result
    const result = [];
    let lastVariationEnd = -1;
    
    // Add main line moves and variations in order
    variations.forEach((variation, idx) => {
      // Add moves from main line up to this variation
      for (let i = lastVariationEnd + 1; i <= variation.startIndex; i++) {
        if (i < moveGroups.length) {
          result.push(moveGroups[i]);
        }
      }
      
      // Update the lastVariationEnd
      lastVariationEnd = variation.startIndex;
      
      // Add the variation
      result.push(
        <div key={`variation-${idx}-${depth}`} className="variation-container">
          {variation.title && <div className="variation-label">{variation.title}</div>}
          <div className="variation-content">
            {renderMoveList(variation.moves, true, depth + 1)}
          </div>
        </div>
      );
    });
    
    // Add any remaining main line moves
    for (let i = lastVariationEnd + 1; i < moveGroups.length; i++) {
      result.push(moveGroups[i]);
    }
    
    return result;
  };
  
  // Render an individual move item
  const renderMoveItem = (move: Move & { originalIndex: number }, index: number) => {
    const isCurrentMove = index === currentMoveIndex;
    const colorClass = move.isWhite ? 'white-move' : 'black-move';
    const isVariationMove = index < 0; // Negative index indicates a variation move
    
    return (
      <span
        className={`move-item ${colorClass} ${isCurrentMove ? 'current-move' : ''}`}
        onClick={() => !isVariationMove && onMoveClick(index)}
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