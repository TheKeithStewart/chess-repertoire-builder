import { Chess } from 'chess.js';
import { type GameMetadata } from '../components/GameMetadataPanel';

export interface PGNGame {
  headers: { [key: string]: string };
  moves: string[];
  comments: { [moveIndex: number]: string };
}

export class PGNProcessor {
  static parsePGN(pgnContent: string): PGNGame | null {
    try {
      const game = new Chess();
      const lines = pgnContent.split('\n');
      const headers: { [key: string]: string } = {};
      const moves: string[] = [];
      const comments: { [moveIndex: number]: string } = {};
      
      let inHeaders = true;
      let gameContent = '';
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        
        if (trimmedLine.startsWith('[') && trimmedLine.endsWith(']')) {
          // Parse header
          const headerMatch = trimmedLine.match(/\[(\w+)\s+"(.*)"\]/);
          if (headerMatch) {
            headers[headerMatch[1]] = headerMatch[2];
          }
        } else if (trimmedLine === '') {
          inHeaders = false;
        } else if (!inHeaders) {
          gameContent += trimmedLine + ' ';
        }
      }
      
      // Parse moves from game content
      const tokens = gameContent.split(/\s+/).filter(token => token.length > 0);
      let moveIndex = 0;
      
      for (const token of tokens) {
        // Skip move numbers
        if (token.match(/^\d+\.+$/)) {
          continue;
        }
        
        // Check for comments
        if (token.startsWith('{') && token.endsWith('}')) {
          const comment = token.slice(1, -1);
          comments[moveIndex - 1] = comment;
          continue;
        }
        
        // Skip result indicators
        if (token === '1-0' || token === '0-1' || token === '1/2-1/2' || token === '*') {
          continue;
        }
        
        // Try to parse as a move
        try {
          const moveObj = game.move(token);
          if (moveObj) {
            moves.push(moveObj.san);
            moveIndex++;
          }
        } catch (e) {
          // Ignore invalid moves
        }
      }
      
      return { headers, moves, comments };
    } catch (error) {
      console.error('Error parsing PGN:', error);
      return null;
    }
  }
  
  static generatePGN(
    metadata: GameMetadata,
    moves: string[],
    comments: { [moveIndex: number]: string }
  ): string {
    const today = new Date().toISOString().split('T')[0];
    
    // Build headers
    const headers = [
      `[Event "${metadata.event}"]`,
      `[Site "${metadata.site || 'Chess Repertoire Builder'}"]`,
      `[Date "${metadata.date || today}"]`,
      `[White "${metadata.white}"]`,
      `[Black "${metadata.black}"]`,
      `[Result "${metadata.result}"]`,
      `[StudyName "${metadata.studyName}"]`,
      `[ChapterName "${metadata.chapterName}"]`
    ];
    
    let pgn = headers.join('\n') + '\n\n';
    
    // Add moves with comments
    const game = new Chess();
    for (let i = 0; i < moves.length; i++) {
      const move = moves[i];
      const moveObj = game.move(move);
      
      if (moveObj) {
        const moveNumber = Math.ceil((i + 1) / 2);
        const isWhite = i % 2 === 0;
        
        if (isWhite) {
          pgn += `${moveNumber}. ${moveObj.san}`;
        } else {
          pgn += ` ${moveObj.san}`;
        }
        
        // Add comment if exists
        if (comments[i]) {
          pgn += ` {${comments[i]}}`;
        }
        
        if (!isWhite) {
          pgn += ' ';
        }
      }
    }
    
    pgn += ` ${metadata.result}`;
    
    return pgn;
  }
  
  static downloadPGN(content: string, filename: string = 'game.pgn') {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
  
  static async splitPGNForChessable(pgnContent: string): Promise<{ [chapterName: string]: string }> {
    // This is a simplified version of the Python splitting logic
    // In a real implementation, you would need to parse variations and split them
    const parsedGame = this.parsePGN(pgnContent);
    if (!parsedGame) {
      throw new Error('Failed to parse PGN');
    }
    
    // For now, return the original PGN as a single chapter
    // TODO: Implement proper variation splitting
    const chapterName = parsedGame.headers.ChapterName || 'Main Line';
    return { [chapterName]: pgnContent };
  }
}