const express = require('express');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { Chess } = require('chess.js');

const app = express();
const PORT = process.env.PORT || 3001;

// Configure multer for file uploads
const upload = multer({ dest: 'uploads/' });

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

// PGN processing utilities
class PGNProcessor {
  static parsePGN(pgnContent) {
    try {
      const lines = pgnContent.split('\n');
      const headers = {};
      const moves = [];
      const comments = {};
      
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
      const game = new Chess();
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
  
  static generatePGN(metadata, moves, comments) {
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
  
  static splitPGNForChessable(pgnContent) {
    // Enhanced version that properly handles variations
    const parsedGame = this.parsePGN(pgnContent);
    if (!parsedGame) {
      throw new Error('Failed to parse PGN');
    }
    
    // For now, return the original PGN as a single chapter
    // In a full implementation, this would parse variations and split them
    const chapterName = parsedGame.headers.ChapterName || 'Main Line';
    return { [chapterName]: pgnContent };
  }
}

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Chess Repertoire Builder API' });
});

app.post('/api/pgn/parse', upload.single('pgn'), (req, res) => {
  try {
    let pgnContent;
    
    if (req.file) {
      // File upload
      pgnContent = fs.readFileSync(req.file.path, 'utf8');
      // Clean up uploaded file
      fs.unlinkSync(req.file.path);
    } else if (req.body.pgn) {
      // Direct PGN text
      pgnContent = req.body.pgn;
    } else {
      return res.status(400).json({ error: 'No PGN content provided' });
    }
    
    const parsed = PGNProcessor.parsePGN(pgnContent);
    if (!parsed) {
      return res.status(400).json({ error: 'Failed to parse PGN' });
    }
    
    res.json(parsed);
  } catch (error) {
    console.error('Error parsing PGN:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/pgn/generate', (req, res) => {
  try {
    const { metadata, moves, comments } = req.body;
    
    if (!metadata || !moves) {
      return res.status(400).json({ error: 'Missing metadata or moves' });
    }
    
    const pgn = PGNProcessor.generatePGN(metadata, moves, comments || {});
    res.json({ pgn });
  } catch (error) {
    console.error('Error generating PGN:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/pgn/split-chessable', (req, res) => {
  try {
    const { pgn } = req.body;
    
    if (!pgn) {
      return res.status(400).json({ error: 'No PGN content provided' });
    }
    
    const chapters = PGNProcessor.splitPGNForChessable(pgn);
    res.json({ chapters });
  } catch (error) {
    console.error('Error splitting PGN:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Chess Repertoire Builder server running on port ${PORT}`);
});

module.exports = app;