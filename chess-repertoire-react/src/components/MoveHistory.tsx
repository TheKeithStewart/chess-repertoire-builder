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
  const renderMove = (move: Move, index: number) => {
    const isCurrentMove = index === currentMoveIndex;
    const className = `move-item ${isCurrentMove ? 'current-move' : ''}`;
    
    return (
      <span
        key={index}
        className={className}
        onClick={() => onMoveClick(index)}
        title={move.comment || ''}
      >
        {move.moveNumber && move.isWhite && (
          <span className="move-number">{move.moveNumber}.</span>
        )}
        {move.moveNumber && !move.isWhite && (
          <span className="move-number">{move.moveNumber}...</span>
        )}
        <span className="move-san">{move.san}</span>
        {move.comment && <span className="move-comment-indicator">💭</span>}
      </span>
    );
  };

  return (
    <div className="move-history">
      <h3>Move History</h3>
      <div className="move-list">
        {moves.length === 0 ? (
          <p className="no-moves">No moves yet. Start playing!</p>
        ) : (
          moves.map((move, index) => renderMove(move, index))
        )}
      </div>
    </div>
  );
};

export default MoveHistory;
export type { Move };