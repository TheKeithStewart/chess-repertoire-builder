import { Chess } from 'chess.js';
import { type GameMetadata } from '../components/GameMetadataPanel';

export interface PGNMove {
  san: string;
  comment?: string;
  variations?: PGNMove[][];
}

export interface PGNGame {
  headers: { [key: string]: string };
  moves: PGNMove[];
  comments: { [moveIndex: number]: string };
}

export class PGNProcessor {
  static parsePGN(pgnContent: string): PGNGame | null {
    try {
      const lines = pgnContent.split('\n');
      const headers: { [key: string]: string } = {};
      
      let inHeaders = true;
      let gameContent = '';
      
      // Parse headers first
      for (const line of lines) {
        const trimmedLine = line.trim();
        
        if (trimmedLine.startsWith('[') && trimmedLine.endsWith(']')) {
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
      
      // Parse moves with variations
      const parsedMoves = this.parseMovesWithVariations(gameContent);
      
      return { 
        headers, 
        moves: parsedMoves,
        comments: {} // We'll handle comments within moves now
      };
    } catch (error) {
      console.error('Error parsing PGN:', error);
      return null;
    }
  }

  private static parseMovesWithVariations(gameContent: string): PGNMove[] {
    const moves: PGNMove[] = [];
    const tokens = this.tokenizePGN(gameContent);
    let currentPosition = 0;
    
    const game = new Chess();
    
    while (currentPosition < tokens.length) {
      const result = this.parseMove(tokens, currentPosition, game);
      if (result.move) {
        moves.push(result.move);
        currentPosition = result.nextPosition;
      } else {
        currentPosition++;
      }
    }
    
    return moves;
  }

  private static tokenizePGN(content: string): string[] {
    // Split on whitespace but keep parentheses and braces as separate tokens
    const tokens: string[] = [];
    let current = '';
    let inComment = false;
    
    for (let i = 0; i < content.length; i++) {
      const char = content[i];
      
      if (char === '{') {
        if (current.trim()) {
          tokens.push(current.trim());
          current = '';
        }
        current = '{';
        inComment = true;
      } else if (char === '}' && inComment) {
        current += '}';
        tokens.push(current);
        current = '';
        inComment = false;
      } else if (inComment) {
        current += char;
      } else if (char === '(' || char === ')') {
        if (current.trim()) {
          tokens.push(current.trim());
          current = '';
        }
        tokens.push(char);
      } else if (/\s/.test(char)) {
        if (current.trim()) {
          tokens.push(current.trim());
          current = '';
        }
      } else {
        current += char;
      }
    }
    
    if (current.trim()) {
      tokens.push(current.trim());
    }
    
    return tokens.filter(token => token.length > 0);
  }

  private static parseMove(tokens: string[], startPos: number, game: Chess): { move: PGNMove | null; nextPosition: number } {
    let pos = startPos;
    
    // Skip move numbers
    while (pos < tokens.length && tokens[pos].match(/^\d+\.+$/)) {
      pos++;
    }
    
    if (pos >= tokens.length) {
      return { move: null, nextPosition: pos };
    }
    
    const token = tokens[pos];
    
    // Skip result indicators
    if (token === '1-0' || token === '0-1' || token === '1/2-1/2' || token === '*') {
      return { move: null, nextPosition: pos + 1 };
    }
    
    // Handle comments (skip for now, we'll associate them with moves later)
    if (token.startsWith('{') && token.endsWith('}')) {
      return { move: null, nextPosition: pos + 1 };
    }
    
    // Handle variations in parentheses
    if (token === '(') {
      return { move: null, nextPosition: pos + 1 };
    }
    
    if (token === ')') {
      return { move: null, nextPosition: pos + 1 };
    }
    
    // Try to parse as a move
    try {
      const tempGame = new Chess(game.fen());
      const moveObj = tempGame.move(token);
      if (moveObj) {
        // Create the move and advance the main game state
        game.move(token);
        
        let comment: string | undefined;
        let variations: PGNMove[][] = [];
        pos++;
        
        // Look for comment immediately after the move
        if (pos < tokens.length && tokens[pos].startsWith('{') && tokens[pos].endsWith('}')) {
          comment = tokens[pos].slice(1, -1);
          pos++;
        }
        
        // Look for variations
        while (pos < tokens.length && tokens[pos] === '(') {
          const variationResult = this.parseVariation(tokens, pos, new Chess(game.fen()));
          if (variationResult.variation.length > 0) {
            variations.push(variationResult.variation);
          }
          pos = variationResult.nextPosition;
        }
        
        const pgnMove: PGNMove = {
          san: moveObj.san,
          comment,
          variations: variations.length > 0 ? variations : undefined
        };
        
        return { move: pgnMove, nextPosition: pos };
      }
    } catch (e) {
      // Invalid move, skip
    }
    
    return { move: null, nextPosition: pos + 1 };
  }

  private static parseVariation(tokens: string[], startPos: number, game: Chess): { variation: PGNMove[]; nextPosition: number } {
    const variation: PGNMove[] = [];
    let pos = startPos;
    
    // Skip opening parenthesis
    if (tokens[pos] === '(') {
      pos++;
    }
    
    let parenCount = 1;
    
    while (pos < tokens.length && parenCount > 0) {
      const token = tokens[pos];
      
      if (token === '(') {
        parenCount++;
        pos++;
      } else if (token === ')') {
        parenCount--;
        pos++;
      } else {
        const result = this.parseMove(tokens, pos, game);
        if (result.move) {
          variation.push(result.move);
        }
        pos = result.nextPosition;
      }
    }
    
    return { variation, nextPosition: pos };
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
    
    // Add moves with comments (keeping backward compatibility for now)
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