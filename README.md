# Chessable Course Builder

This toolkit provides two ways to create and manage chess repertoires for Chessable:

1. **GUI Chess Board Editor**: Build your repertoire locally with an interactive chess board
2. **PGN Converter**: Convert Lichess studies into Chessable-ready PGN files

## Overview

When creating opening repertoires, you need a way to organize complex variations into separate chapters for Chessable. This toolkit offers a complete workflow:

- Use the built-in **Chess Board GUI** to create and edit your repertoire directly
- Or use **Lichess** to build your repertoire and then convert it with this tool
- Export to separate PGN files optimized for Chessable chapters

## Features

- Splits a Lichess PGN file into separate PGN files for each major variation
- Preserves all comments, annotations, and analysis
- Names chapters based on variation comments
- Maintains all original metadata from the Lichess PGN
- Works with standard opening repertoire studies

## Requirements

- Python 3.6 or higher
- Required packages (installed automatically):
  - python-chess: Chess library for move validation and PGN handling
  - pillow: Image processing for the GUI
  - cairosvg: SVG rendering for chess pieces

## Installation

### Easy Setup (macOS)

1. Clone this repository or download the scripts
2. Run the setup script:

```
./setup_mac.sh
```

This will install all required dependencies including Cairo libraries needed for the GUI.

### Manual Setup

1. Clone this repository or download the scripts
2. Install Cairo dependencies:
   - macOS: `brew install cairo pango`
   - Linux: `apt-get install libcairo2-dev pkg-config python3-dev`
3. Install the required Python packages:

```
pip install -r requirements.txt
```

## Usage

### Interactive GUI Editor

Start the GUI application to create and edit your chess repertoire:

```
./run_gui.sh
```

Or manually:

```
python chessable_gui.py
```

### PGN Converter (Command Line)

Convert a Lichess PGN to Chessable chapters:

```
python split_pgn_for_chessable.py your_lichess_study.pgn
```

This will create an `output` directory with separate PGN files for each variation.

With custom output directory:

```
python split_pgn_for_chessable.py your_lichess_study.pgn -o custom_directory
```

## How It Works

The script analyzes your PGN file and intelligently identifies the first position in the game that contains multiple variations. Each variation becomes its own separate PGN file, with the variation name derived from the variation comment.

You can control where variations are split using two methods:

### Method 1: Automatic Detection

The script automatically detects the structure of Lichess PGN files, finding the first position that has alternative variations (shown in parentheses in the PGN). This works perfectly with the standard Lichess export format.

For example, in a Queen's Gambit repertoire from Lichess:

```
1. d4 d5 2. c4 dxc4 { Queen's Gambit Accepted } (2... c6 { Queen's Gambit Declined - Slav Defense }) (2... e6 { Queen's Gambit Declined })
```

The script will automatically detect that move 2 is the branching point and split into separate chapters:
- 00_Main_Line_-_Queens_Gambit_Accepted.pgn (with the dxc4 line)
- 01_Queens_Gambit_Declined_-_Slav_Defense.pgn (with the c6 line)
- 02_Queens_Gambit_Declined.pgn (with the e6 line)

The main line and all alternative moves at the same position become separate chapters, preserving all comments and annotations.

### Method 2: Using Split Markers

For precise control, you can add a special comment marker `[SPLIT_CHAPTERS]` in your PGN at exactly the position where you want variations to be split.

For example:
```
1. e4 c5 2. Nf3 { [SPLIT_CHAPTERS] Split after this move } d6 (2... Nc6) (2... e6)
```

This would create separate chapters for:
- 2...d6 (Main Line)
- 2...Nc6 (Variation 1)
- 2...e6 (Variation 2)

To use the split marker in Lichess:
1. Add the marker text `[SPLIT_CHAPTERS]` to any move comment
2. Export the PGN from Lichess
3. Run the script on the exported PGN
4. Each variation at the marked position becomes a separate chapter

## Workflow

1. Create and refine your opening repertoire in Lichess
2. Export the PGN from Lichess
3. Run this script on the PGN
4. Import the generated PGN files into Chessable as separate chapters

## GUI Features

The Chess Board GUI provides an intuitive way to build and manage your chess repertoire:

### Interactive Chess Board
- Click to select and move pieces
- Highlighted legal moves
- Support for piece promotion
- Flip board orientation

### Variation Management
- Create and navigate variations easily
- Visual move tree showing all lines
- Add comments to any position
- Set chapter names and metadata

### Import/Export
- Load existing PGN files (including from Lichess)
- Save your work as standard PGN
- Export chapters directly to Chessable-ready format

### Workflow with the GUI

1. Start the GUI with `./run_gui.sh`
2. Create your repertoire by making moves on the board
3. Add variations by navigating back to a position and making a different move
4. Add comments to explain the ideas behind moves
5. Set chapter and study names in the interface
6. Export for Chessable when ready

## Limitations

- May not preserve all complex nested annotations in all cases
- For very complex studies, manual inspection of the output files is recommended
- Special chess symbols and diagrams may need adjustment in Chessable

## License

MIT
