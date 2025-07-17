# Chess Repertoire Builder - React Web Application

A modern React web application for building and managing chess opening repertoires, converted from the original Python application.

![Chess Repertoire Builder React App](https://github.com/user-attachments/assets/55d40db5-3c96-4988-8f5d-8dafbde5ce80)

## Features

### Core Functionality
- **Interactive Chess Board**: Drag and drop or click-to-move piece interface
- **Move Navigation**: Forward/backward navigation through games
- **PGN Support**: Import and export PGN files
- **Position Comments**: Add notes to specific positions
- **Game Metadata**: Edit game information (Event, Study Name, Chapter, etc.)
- **Board Flipping**: View from White or Black perspective

### Advanced Features
- **Chessable Export**: Split PGN files into chapters for Chessable import
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, intuitive interface built with React
- **Real-time Updates**: Instant feedback when making moves
- **Move History**: Visual representation of all moves played

## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **chess.js** for move validation and game logic
- **react-chessboard** for interactive chess board component
- **Modern CSS** with responsive design

### Backend (Optional)
- **Node.js** with Express.js
- **Multer** for file uploads
- **CORS** for cross-origin requests
- **chess.js** for server-side PGN processing

## Installation

### Prerequisites
- Node.js 16 or higher
- npm or yarn package manager

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/TheKeithStewart/chess-repertoire-builder.git
   cd chess-repertoire-builder/chess-repertoire-react
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   Navigate to `http://localhost:5173`

## Usage

### Creating a New Game
1. Click "New Game" to reset the board
2. Edit game metadata (Event, Study Name, Chapter, etc.)
3. Make moves by clicking and dragging pieces or clicking squares
4. Add comments to positions using the comment panel

### Loading PGN Files
1. Click "Load PGN" and select a PGN file
2. The game will be loaded with all moves and metadata
3. Navigate through moves using the arrow buttons
4. Edit metadata and comments as needed

### Exporting for Chessable
1. Create or load your repertoire
2. Click "Export for Chessable"
3. Multiple PGN files will be downloaded, one per variation
4. Import these files into Chessable as separate chapters

### Navigation Controls
- **⏮️ Start**: Go to the initial position
- **⏪ Back**: Go to the previous move
- **⏩ Forward**: Go to the next move
- **⏭️ End**: Go to the final position
- **Flip Board**: Toggle between White and Black perspective

### Adding Comments
1. Navigate to any position
2. Type your comment in the comment box
3. Click "Save Comment" or press Ctrl+Enter
4. Comments are indicated by 💭 in the move history

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Project Structure
```
chess-repertoire-react/
├── src/
│   ├── components/          # React components
│   │   ├── ChessBoard.tsx   # Interactive chess board
│   │   ├── GameControls.tsx # Game action buttons
│   │   ├── MoveHistory.tsx  # Move list display
│   │   ├── CommentPanel.tsx # Position comments
│   │   └── GameMetadataPanel.tsx # Game information
│   ├── utils/               # Utility functions
│   │   └── pgnProcessor.ts  # PGN parsing and generation
│   ├── App.tsx              # Main application component
│   └── App.css              # Application styles
├── server/                  # Optional backend server
│   ├── server.js            # Express.js server
│   └── package.json         # Server dependencies
└── public/                  # Static assets
```

## Comparison with Python Version

### Advantages of React Version
- **Web-based**: No installation required, works in any browser
- **Responsive**: Adapts to different screen sizes
- **Modern UI**: Clean, intuitive interface
- **Real-time**: Instant updates without page refreshes
- **Portable**: Share links, no platform dependencies

### Feature Parity
- ✅ Interactive chess board with piece movement
- ✅ PGN import/export functionality
- ✅ Position commenting system
- ✅ Game metadata editing
- ✅ Board flipping capability
- ✅ Move navigation (forward/backward)
- ✅ Chessable export functionality
- ⚠️ Engine analysis (planned for future release)
- ⚠️ Advanced variation handling (simplified version)

## Future Enhancements

### Planned Features
- **Stockfish Integration**: Add engine analysis
- **Variation Trees**: Advanced variation management
- **Database Support**: Save games to cloud storage
- **Multiplayer**: Share and collaborate on repertoires
- **Opening Explorer**: Integration with opening databases
- **Training Mode**: Practice your repertoire

### Technical Improvements
- **Service Worker**: Offline functionality
- **PWA**: Install as mobile app
- **WebAssembly**: Faster move generation
- **GraphQL**: More efficient data fetching

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit:
https://github.com/TheKeithStewart/chess-repertoire-builder

---

*Built with ❤️ for the chess community*
