import React from 'react';

interface GameControlsProps {
  onNewGame: () => void;
  onLoadPGN: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSavePGN: () => void;
  onExportChessable: () => void;
  onFlipBoard: () => void;
  onGoBack: () => void;
  onGoForward: () => void;
  onGoToStart: () => void;
  onGoToEnd: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
}

const GameControls: React.FC<GameControlsProps> = ({
  onNewGame,
  onLoadPGN,
  onSavePGN,
  onExportChessable,
  onFlipBoard,
  onGoBack,
  onGoForward,
  onGoToStart,
  onGoToEnd,
  canGoBack,
  canGoForward
}) => {
  return (
    <div className="game-controls">
      <div className="control-section">
        <h3>Game Actions</h3>
        <div className="button-group">
          <button onClick={onNewGame}>New Game</button>
          <button onClick={onSavePGN}>Save PGN</button>
          <button onClick={onExportChessable}>Export for Chessable</button>
        </div>
        <div className="file-input-group">
          <label htmlFor="pgn-file">Load PGN:</label>
          <input
            id="pgn-file"
            type="file"
            accept=".pgn"
            onChange={onLoadPGN}
          />
        </div>
      </div>

      <div className="control-section">
        <h3>Navigation</h3>
        <div className="button-group">
          <button onClick={onGoToStart} disabled={!canGoBack}>
            ⏮️ Start
          </button>
          <button onClick={onGoBack} disabled={!canGoBack}>
            ⏪ Back
          </button>
          <button onClick={onGoForward} disabled={!canGoForward}>
            ⏩ Forward
          </button>
          <button onClick={onGoToEnd} disabled={!canGoForward}>
            ⏭️ End
          </button>
        </div>
        <div className="button-group">
          <button onClick={onFlipBoard}>Flip Board</button>
        </div>
      </div>
    </div>
  );
};

export default GameControls;