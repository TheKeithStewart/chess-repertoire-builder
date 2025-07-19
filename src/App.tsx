import React, { useState, useCallback, useEffect } from 'react';
import { Chess } from 'chess.js';
import ChessBoard from './components/ChessBoard';
import GameControls from './components/GameControls';
import GameMetadataPanel, { type GameMetadata } from './components/GameMetadataPanel';
import MoveHistory, { type Move } from './components/MoveHistory';
import CommentPanel from './components/CommentPanel';
import { PGNProcessor } from './utils/pgnProcessor';
import './App.css';

interface GameState {
  game: Chess;
  moveHistory: Move[];
  currentMoveIndex: number;
  comments: { [moveIndex: number]: string };
}

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>(() => ({
    game: new Chess(),
    moveHistory: [],
    currentMoveIndex: -1,
    comments: {}
  }));

  const [metadata, setMetadata] = useState<GameMetadata>({
    event: 'Chess Repertoire Builder',
    site: 'Chess Repertoire Builder',
    date: new Date().toISOString().split('T')[0],
    studyName: 'My Chess Study',
    chapterName: 'Main Line',
    white: '?',
    black: '?',
    result: '*'
  });

  const [boardOrientation, setBoardOrientation] = useState<'white' | 'black'>('white');
  const [currentPositionComment, setCurrentPositionComment] = useState('');

  // Update current position comment when move index changes
  useEffect(() => {
    const comment = gameState.comments[gameState.currentMoveIndex] || '';
    setCurrentPositionComment(comment);
  }, [gameState.currentMoveIndex, gameState.comments]);

  const handleMove = useCallback((move: string) => {
    const newGame = new Chess(gameState.game.fen());
    const moveObj = newGame.move(move);
    
    if (moveObj) {
      const newMove: Move = {
        move: move,
        san: moveObj.san,
        moveNumber: Math.ceil(gameState.moveHistory.length / 2) + 1,
        isWhite: gameState.moveHistory.length % 2 === 0
      };
      
      const newMoveHistory = [...gameState.moveHistory, newMove];
      const newMoveIndex = newMoveHistory.length - 1;
      
      setGameState({
        game: newGame,
        moveHistory: newMoveHistory,
        currentMoveIndex: newMoveIndex,
        comments: gameState.comments
      });
    }
  }, [gameState]);

  const handleNewGame = useCallback(() => {
    const newGame = new Chess();
    setGameState({
      game: newGame,
      moveHistory: [],
      currentMoveIndex: -1,
      comments: {}
    });
    setCurrentPositionComment('');
  }, []);

  const handleLoadPGN = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const parsedGame = PGNProcessor.parsePGN(content);
        
        if (parsedGame) {
          const newGame = new Chess();
          const newMoveHistory: Move[] = [];
          const newComments: { [moveIndex: number]: string } = {};
          
          // Replay moves
          for (let i = 0; i < parsedGame.moves.length; i++) {
            const moveObj = newGame.move(parsedGame.moves[i]);
            if (moveObj) {
              newMoveHistory.push({
                move: moveObj.from + moveObj.to,
                san: moveObj.san,
                moveNumber: Math.ceil((i + 1) / 2),
                isWhite: i % 2 === 0
              });
              
              if (parsedGame.comments[i]) {
                newComments[i] = parsedGame.comments[i];
              }
            }
          }
          
          // Update metadata
          setMetadata({
            event: parsedGame.headers.Event || 'Chess Repertoire Builder',
            site: parsedGame.headers.Site || 'Chess Repertoire Builder',
            date: parsedGame.headers.Date || new Date().toISOString().split('T')[0],
            studyName: parsedGame.headers.StudyName || 'My Chess Study',
            chapterName: parsedGame.headers.ChapterName || 'Main Line',
            white: parsedGame.headers.White || '?',
            black: parsedGame.headers.Black || '?',
            result: parsedGame.headers.Result || '*'
          });
          
          setGameState({
            game: newGame,
            moveHistory: newMoveHistory,
            currentMoveIndex: newMoveHistory.length - 1,
            comments: newComments
          });
        }
      };
      reader.readAsText(file);
    }
  }, []);

  const handleSavePGN = useCallback(() => {
    const moves = gameState.moveHistory.map(move => move.san);
    const pgnContent = PGNProcessor.generatePGN(metadata, moves, gameState.comments);
    PGNProcessor.downloadPGN(pgnContent, `${metadata.chapterName.replace(/\s+/g, '_')}.pgn`);
  }, [metadata, gameState]);

  const handleExportChessable = useCallback(async () => {
    const moves = gameState.moveHistory.map(move => move.san);
    const pgnContent = PGNProcessor.generatePGN(metadata, moves, gameState.comments);
    
    try {
      const chapters = await PGNProcessor.splitPGNForChessable(pgnContent);
      
      // Download each chapter as a separate file
      Object.entries(chapters).forEach(([chapterName, content], index) => {
        const filename = `${String(index).padStart(2, '0')}_${chapterName.replace(/\s+/g, '_')}.pgn`;
        setTimeout(() => {
          PGNProcessor.downloadPGN(content, filename);
        }, index * 100); // Slight delay to prevent browser blocking
      });
    } catch (error) {
      console.error('Error exporting for Chessable:', error);
      alert('Error exporting for Chessable. Please try again.');
    }
  }, [metadata, gameState]);

  const handleFlipBoard = useCallback(() => {
    setBoardOrientation(prev => prev === 'white' ? 'black' : 'white');
  }, []);

  const handleNavigateToMove = useCallback((moveIndex: number) => {
    const newGame = new Chess();
    
    // Replay moves up to the selected index
    for (let i = 0; i <= moveIndex; i++) {
      if (gameState.moveHistory[i]) {
        newGame.move(gameState.moveHistory[i].san);
      }
    }
    
    setGameState(prev => ({
      ...prev,
      game: newGame,
      currentMoveIndex: moveIndex
    }));
  }, [gameState.moveHistory]);

  const handleGoBack = useCallback(() => {
    if (gameState.currentMoveIndex >= 0) {
      handleNavigateToMove(gameState.currentMoveIndex - 1);
    }
  }, [gameState.currentMoveIndex, handleNavigateToMove]);

  const handleGoForward = useCallback(() => {
    if (gameState.currentMoveIndex < gameState.moveHistory.length - 1) {
      handleNavigateToMove(gameState.currentMoveIndex + 1);
    }
  }, [gameState.currentMoveIndex, gameState.moveHistory.length, handleNavigateToMove]);

  const handleGoToStart = useCallback(() => {
    setGameState(prev => ({
      ...prev,
      game: new Chess(),
      currentMoveIndex: -1
    }));
  }, []);

  const handleGoToEnd = useCallback(() => {
    if (gameState.moveHistory.length > 0) {
      handleNavigateToMove(gameState.moveHistory.length - 1);
    }
  }, [gameState.moveHistory.length, handleNavigateToMove]);

  const handleMetadataChange = useCallback((key: keyof GameMetadata, value: string) => {
    setMetadata(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);

  const handleCommentSave = useCallback((comment: string) => {
    setGameState(prev => ({
      ...prev,
      comments: {
        ...prev.comments,
        [prev.currentMoveIndex]: comment
      }
    }));
    setCurrentPositionComment(comment);
  }, []);

  const canGoBack = gameState.currentMoveIndex >= 0;
  const canGoForward = gameState.currentMoveIndex < gameState.moveHistory.length - 1;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Chess Repertoire Builder</h1>
        <p>Build and organize your chess opening repertoire</p>
      </header>

      <div className="app-content">
        <div className="chess-section">
          <ChessBoard
            game={gameState.game}
            onMove={handleMove}
            boardOrientation={boardOrientation}
          />
        </div>

        <div className="controls-section">
          <GameMetadataPanel
            metadata={metadata}
            onMetadataChange={handleMetadataChange}
          />
          
          <GameControls
            onNewGame={handleNewGame}
            onLoadPGN={handleLoadPGN}
            onSavePGN={handleSavePGN}
            onExportChessable={handleExportChessable}
            onFlipBoard={handleFlipBoard}
            onGoBack={handleGoBack}
            onGoForward={handleGoForward}
            onGoToStart={handleGoToStart}
            onGoToEnd={handleGoToEnd}
            canGoBack={canGoBack}
            canGoForward={canGoForward}
          />
          
          <MoveHistory
            moves={gameState.moveHistory}
            currentMoveIndex={gameState.currentMoveIndex}
            onMoveClick={handleNavigateToMove}
          />
          
          <CommentPanel
            currentComment={currentPositionComment}
            onCommentSave={handleCommentSave}
          />
        </div>
      </div>
    </div>
  );
};

export default App;
