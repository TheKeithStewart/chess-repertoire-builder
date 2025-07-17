import React from 'react';

interface GameMetadata {
  event: string;
  site: string;
  date: string;
  studyName: string;
  chapterName: string;
  white: string;
  black: string;
  result: string;
}

interface GameMetadataProps {
  metadata: GameMetadata;
  onMetadataChange: (key: keyof GameMetadata, value: string) => void;
}

const GameMetadataPanel: React.FC<GameMetadataProps> = ({
  metadata,
  onMetadataChange
}) => {
  const handleChange = (key: keyof GameMetadata) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    onMetadataChange(key, event.target.value);
  };

  return (
    <div className="game-metadata">
      <h3>Game Information</h3>
      <div className="metadata-grid">
        <div className="metadata-row">
          <label htmlFor="event">Event:</label>
          <input
            id="event"
            type="text"
            value={metadata.event}
            onChange={handleChange('event')}
          />
        </div>
        
        <div className="metadata-row">
          <label htmlFor="study-name">Study Name:</label>
          <input
            id="study-name"
            type="text"
            value={metadata.studyName}
            onChange={handleChange('studyName')}
          />
        </div>
        
        <div className="metadata-row">
          <label htmlFor="chapter-name">Chapter:</label>
          <input
            id="chapter-name"
            type="text"
            value={metadata.chapterName}
            onChange={handleChange('chapterName')}
          />
        </div>
        
        <div className="metadata-row">
          <label htmlFor="white">White:</label>
          <input
            id="white"
            type="text"
            value={metadata.white}
            onChange={handleChange('white')}
          />
        </div>
        
        <div className="metadata-row">
          <label htmlFor="black">Black:</label>
          <input
            id="black"
            type="text"
            value={metadata.black}
            onChange={handleChange('black')}
          />
        </div>
        
        <div className="metadata-row">
          <label htmlFor="result">Result:</label>
          <input
            id="result"
            type="text"
            value={metadata.result}
            onChange={handleChange('result')}
          />
        </div>
      </div>
    </div>
  );
};

export default GameMetadataPanel;
export type { GameMetadata };