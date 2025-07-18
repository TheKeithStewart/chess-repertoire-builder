import React from 'react';

interface Move {
  move: string;
  san: string;
  comment?: string;
  moveNumber?: number;
  isWhite?: boolean;
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
  // Process moves into a proper PGN-style display with move pairs
  const renderMoveList = () => {
    if (moves.length === 0) {
      return <p className="no-moves">No moves yet. Start playing!</p>;
    }

    // Check if we have any moves to process
    
    // Process all moves and ensure we have consistent isWhite values
    const normalizedMoves = moves.map((move, index) => {
      // Use the explicitly provided isWhite if available, otherwise calculate based on index
      let isWhite = move.isWhite !== undefined ? move.isWhite : index % 2 === 0;
      
      return {
        ...move,
        isWhite,
        originalIndex: index  // Keep track of original index for onClick
      };
    });

    // Build move groupings based on the actual move sequence
    // This will ensure that White and Black moves are properly paired together in standard chess notation
    // For the Queens Gambit, we want:
    // 1. d4 d5
    // 2. c4 dxc4
    // Instead of what we're seeing:
    // 1. d4 d5
    // 2. c4
    // 3. ... dxc4
    
    const movesByNumber: { [key: number]: { white?: Move & { originalIndex: number }, black?: Move & { originalIndex: number } } } = {};
    
    // Determine the correct move number for each half-move
    let currentMoveNumber = 1;
    let expectingWhite = true;
    
    for (let i = 0; i < normalizedMoves.length; i++) {
      const move = normalizedMoves[i];
      const isWhiteMove = move.isWhite;
      
      // Initialize the move number entry if it doesn't exist
      if (!movesByNumber[currentMoveNumber]) {
        movesByNumber[currentMoveNumber] = {};
      }
      
      // Add the move to the correct color slot
      if (isWhiteMove) {
        movesByNumber[currentMoveNumber].white = move as Move & { originalIndex: number };
        expectingWhite = false; // Next move should be Black's
      } else {
        movesByNumber[currentMoveNumber].black = move as Move & { originalIndex: number };
        currentMoveNumber++; // Increment move number after Black's move
        expectingWhite = true; // Next move should be White's
      }
    }

    // Create move pairs with correct numbering and notation
    return Object.entries(movesByNumber).map(([moveNum, pair]) => {
      const moveNumber = parseInt(moveNum);
      
      return (
        <div key={`move-${moveNumber}`} className="move-group">
          {/* Always show the move number */}
          <span className="move-number-label">{moveNumber}.</span>
          
          {/* Show White's move if available */}
          {pair.white && renderMoveItem(pair.white, pair.white.originalIndex)}
          
          {/* Show Black's move with proper ellipsis if needed */}
          {pair.black && (
            <>
              {!pair.white && (
                // For Black's move without a preceding White move in the same number,
                // we need to show the ellipsis after the move number (1...)
                <span className="move-ellipsis">...</span>
              )}
              {renderMoveItem(pair.black, pair.black.originalIndex)}
            </>
          )}
        </div>
      );
    });
  };
  
  // Render an individual move item
  const renderMoveItem = (move: Move & { originalIndex: number }, index: number) => {
    const isCurrentMove = index === currentMoveIndex;
    const colorClass = move.isWhite ? 'white-move' : 'black-move';
    
    return (
      <span
        className={`move-item ${colorClass} ${isCurrentMove ? 'current-move' : ''}`}
        onClick={() => onMoveClick(index)}
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