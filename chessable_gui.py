#!/usr/bin/env python3
"""
Chessable Course Builder

A GUI application for building chess variations and exporting them as 
Chessable-ready PGN files.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import _tkinter
import chess
import chess.pgn
import chess.svg
import chess.engine
from PIL import Image, ImageTk
import io
import cairosvg
from datetime import datetime
import re
import threading
import subprocess
import platform
import shutil
from split_pgn_for_chessable import process_pgn

class ChessSquare(tk.Canvas):
    """A canvas representing a square on the chess board."""
    def __init__(self, master, size, row, col, color, **kwargs):
        super().__init__(master, width=size, height=size, bd=0, highlightthickness=0, **kwargs)
        self.size = size
        self.row = row
        self.col = col
        self.color = color
        self.piece = None
        self.highlight = False
        self._draw()
        
    def _draw(self):
        self.delete("all")
        # Draw the square
        fill_color = "#f0d9b5" if self.color == 'light' else "#b58863"
        if self.highlight:
            fill_color = "#aaa23b" if self.color == 'light' else "#cdd26a"
        self.create_rectangle(0, 0, self.size, self.size, fill=fill_color, outline="")
        
        # Draw the piece if there is one
        if self.piece:
            self.create_image(self.size//2, self.size//2, image=self.piece)
            
    def set_piece(self, piece_img):
        self.piece = piece_img
        self._draw()
        
    def set_highlight(self, highlight):
        self.highlight = highlight
        self._draw()

class ChessboardGUI(tk.Frame):
    """Main chess board GUI component."""
    def add_engine_line(self):
        """Add the current engine-suggested move to the game."""
        if not self.engine_path or not hasattr(self, 'engine_info_var'):
            return
            
        # Extract the best move from the engine info
        engine_info = self.engine_info_var.get()
        if "Best:" not in engine_info:
            messagebox.showinfo("No Engine Move", 
                              "No engine move available. Start analysis first.")
            return
            
        # Get the move in SAN format
        best_move_part = engine_info.split("Best:")[1].strip()
        best_move_san = best_move_part.split()[0]  # Get first word after "Best:"
        
        try:
            # Find the move object from SAN
            for move in self.board.legal_moves:
                if self.board.san(move) == best_move_san:
                    # Make the move
                    self.make_move(move)
                    return
                    
            messagebox.showinfo("Move Error", 
                              f"Could not find move {best_move_san} in legal moves.")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding engine line: {str(e)}")
    
    def __init__(self, master, square_size=64):
        super().__init__(master)
        self.master = master
        self.square_size = square_size
        self.selected_square = None
        self.legal_moves = []
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.current_node = self.game
        self.engine = None
        self.engine_path = None
        self.analysis_running = False
        self.analysis_thread = None
        self.setup_board()
        self.load_piece_images()
        self.create_board_widgets()
        self.create_control_panel()
        self.variation_tree = VariationTree(self, self.controls_frame)
        self.variation_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.find_stockfish()
        self.update_board()
        
        # Now bind the engine line button since add_engine_line method is defined
        if self.engine_path and hasattr(self, 'engine_line_button'):
            self.engine_line_button.config(command=self.add_engine_line)

    def setup_board(self):
        """Initialize the chess board."""
        self.game.headers["Event"] = "Chessable Course Builder"
        self.game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        self.game.headers["White"] = "?"
        self.game.headers["Black"] = "?"
        self.game.headers["Result"] = "*"

    def load_piece_images(self):
        """Load the chess piece images."""
        self.piece_images = {}
        piece_size = int(self.square_size * 0.8)
        pieces = ['p', 'r', 'n', 'b', 'q', 'k', 'P', 'R', 'N', 'B', 'Q', 'K']
        
        for piece in pieces:
            color = 'w' if piece.isupper() else 'b'
            piece_type = piece.lower()
            svg_data = chess.svg.piece(chess.Piece.from_symbol(piece), size=piece_size)
            png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
            img = Image.open(io.BytesIO(png_data))
            self.piece_images[piece] = ImageTk.PhotoImage(img)

    def create_board_widgets(self):
        """Create the chess board UI."""
        self.board_frame = tk.Frame(self)
        self.board_frame.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.squares = {}
        for row in range(8):
            for col in range(8):
                color = 'light' if (row + col) % 2 == 0 else 'dark'
                square = ChessSquare(self.board_frame, self.square_size, 7-row, col, color)
                square.grid(row=row, column=col)
                square.bind("<Button-1>", lambda e, r=7-row, c=col: self.on_square_click(r, c))
                self.squares[(7-row, col)] = square
                
        # Add rank and file labels
        for i in range(8):
            # Rank labels
            tk.Label(self.board_frame, text=str(i+1)).grid(row=7-i, column=8)
            # File labels
            tk.Label(self.board_frame, text=chr(97+i)).grid(row=8, column=i)

    def create_control_panel(self):
        """Create the control panel with buttons and move list."""
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Metadata frame
        metadata_frame = tk.LabelFrame(self.controls_frame, text="Game Information")
        metadata_frame.pack(fill=tk.X, pady=10)
        
        # Event name
        tk.Label(metadata_frame, text="Event:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.event_var = tk.StringVar(value="Chessable Course Builder")
        tk.Entry(metadata_frame, textvariable=self.event_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Study name
        tk.Label(metadata_frame, text="Study Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.study_var = tk.StringVar(value="My Chess Study")
        tk.Entry(metadata_frame, textvariable=self.study_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Chapter name
        tk.Label(metadata_frame, text="Chapter:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.chapter_var = tk.StringVar(value="Main Line")
        tk.Entry(metadata_frame, textvariable=self.chapter_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        metadata_frame.columnconfigure(1, weight=1)
        
        # Navigation buttons
        nav_frame = tk.Frame(self.controls_frame)
        nav_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(nav_frame, text="<<", command=self.go_to_start).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="<", command=self.go_back).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text=">", command=self.go_forward).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text=">>", command=self.go_to_end).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Flip Board", command=self.flip_board).pack(side=tk.RIGHT, padx=2)
        
        # Comment area
        comment_frame = tk.LabelFrame(self.controls_frame, text="Comments")
        comment_frame.pack(fill=tk.X, pady=10)
        
        self.comment_text = tk.Text(comment_frame, height=4, width=40, wrap=tk.WORD)
        self.comment_text.pack(fill=tk.BOTH, padx=5, pady=5)
        tk.Button(comment_frame, text="Save Comment", command=self.save_comment).pack(pady=5)
        
        # Engine analysis frame
        engine_frame = tk.LabelFrame(self.controls_frame, text="Stockfish Analysis")
        engine_frame.pack(fill=tk.X, pady=10)
        
        # Engine status and info
        self.engine_info_var = tk.StringVar(value="Engine not running")
        engine_info_label = tk.Label(engine_frame, textvariable=self.engine_info_var, 
                                    font=("TkDefaultFont", 10), anchor="w")
        engine_info_label.pack(fill=tk.X, padx=5, pady=5)
        
        engine_btn_frame = tk.Frame(engine_frame)
        engine_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        if self.engine_path:
            self.analysis_button = tk.Button(engine_btn_frame, text="Start Analysis", command=self.start_analysis)
            self.analysis_button.pack(side=tk.LEFT, padx=5)
            
            # Only show this button if engine is available
            self.engine_line_button = tk.Button(engine_btn_frame, text="Add Engine Line")
            self.engine_line_button.pack(side=tk.LEFT, padx=5)
            # We'll bind this later after the add_engine_line method is defined
        else:
            self.analysis_button = tk.Button(engine_btn_frame, text="Install Stockfish", command=self.install_stockfish)
            self.analysis_button.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        button_frame = tk.Frame(self.controls_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="New Game", command=self.new_game).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Load PGN", command=self.load_pgn).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save PGN", command=self.save_pgn).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Export for Chessable", command=self.export_chessable).pack(side=tk.RIGHT, padx=5)
        
        # No duplicate engine frame needed - already created above

    def update_board(self):
        """Update the board display to match the current position."""
        for row in range(8):
            for col in range(8):
                square = self.squares[(row, col)]
                square.set_highlight(False)
                
                # Get the piece at this position
                piece = self.board.piece_at(chess.square(col, row))
                if piece:
                    square.set_piece(self.piece_images[piece.symbol()])
                else:
                    square.set_piece(None)
                    
        # Update selected square and legal moves
        if self.selected_square:
            row, col = self.selected_square
            self.squares[(row, col)].set_highlight(True)
            for move in self.legal_moves:
                to_row = chess.square_rank(move.to_square)
                to_col = chess.square_file(move.to_square)
                self.squares[(to_row, to_col)].set_highlight(True)
        
        # Update headers
        self.game.headers["Event"] = self.event_var.get()
        self.game.headers["StudyName"] = self.study_var.get()
        self.game.headers["ChapterName"] = self.chapter_var.get()
        
        # Update comment field
        self.comment_text.delete(1.0, tk.END)
        if self.current_node.comment:
            self.comment_text.insert(tk.END, self.current_node.comment)
            
        # Update variation tree
        self.variation_tree.update_tree(self.game, self.current_node)
        
        # Update engine analysis if running
        if self.analysis_running:
            # We don't need to restart the analysis as it continuously evaluates the current position
            pass
        else:
            # Clear engine info
            self.engine_info_var.set("Engine not running")

    def on_square_click(self, row, col):
        """Handle clicks on the chess board squares."""
        square = chess.square(col, row)
        
        if self.selected_square:
            # Check if this is a legal target square
            from_square = chess.square(self.selected_square[1], self.selected_square[0])
            move = chess.Move(from_square, square)
            
            # Check for promotion
            if move in self.legal_moves and self.board.piece_at(from_square).piece_type == chess.PAWN:
                if (row == 0 and self.board.piece_at(from_square).color == chess.WHITE) or \
                   (row == 7 and self.board.piece_at(from_square).color == chess.BLACK):
                    promotion_piece = self.get_promotion_choice()
                    if promotion_piece:
                        move = chess.Move(from_square, square, promotion=promotion_piece)
            
            if move in self.legal_moves:
                # Make the move and update the game tree
                self.make_move(move)
                self.selected_square = None
                self.legal_moves = []
            else:
                # Check if clicked on another piece of the same color
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = (row, col)
                    self.legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
                else:
                    self.selected_square = None
                    self.legal_moves = []
        else:
            # Select the square if it has a piece of the correct color
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = (row, col)
                self.legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        
        self.update_board()

    def get_promotion_choice(self):
        """Ask the user what piece to promote to."""
        pieces = {
            "Queen": chess.QUEEN,
            "Rook": chess.ROOK,
            "Bishop": chess.BISHOP,
            "Knight": chess.KNIGHT
        }
        choice = simpledialog.askstring("Promotion", "Promote to: (Queen, Rook, Bishop, Knight)",
                                        parent=self.master)
        if choice:
            choice = choice.strip().capitalize()
            return pieces.get(choice, chess.QUEEN)  # Default to Queen
        return None

    def make_move(self, move):
        """Make a move on the board and update the game tree."""
        # Check if this move exists in the current variations
        for variation in self.current_node.variations:
            if variation.move == move:
                # Move already exists, just navigate to it
                self.current_node = variation
                self.board.push(move)
                return
        
        # Add a new move
        new_node = self.current_node.add_variation(move)
        self.current_node = new_node
        self.board.push(move)

    def go_back(self):
        """Navigate to the previous move."""
        if self.current_node.parent:
            self.board.pop()
            self.current_node = self.current_node.parent
            self.selected_square = None
            self.legal_moves = []
            self.update_board()

    def go_forward(self):
        """Navigate to the next move in the main line."""
        if self.current_node.variations:
            move = self.current_node.variations[0].move
            self.board.push(move)
            self.current_node = self.current_node.variations[0]
            self.selected_square = None
            self.legal_moves = []
            self.update_board()

    def go_to_start(self):
        """Go back to the starting position."""
        while self.current_node.parent:
            self.board.pop()
            self.current_node = self.current_node.parent
        self.selected_square = None
        self.legal_moves = []
        self.update_board()

    def go_to_end(self):
        """Go to the end of the current line."""
        while self.current_node.variations:
            move = self.current_node.variations[0].move
            self.board.push(move)
            self.current_node = self.current_node.variations[0]
        self.selected_square = None
        self.legal_moves = []
        self.update_board()

    def flip_board(self):
        """Flip the board view."""
        # Store the current board state
        current_positions = {}
        for row in range(8):
            for col in range(8):
                square = self.squares[(row, col)]
                current_positions[(row, col)] = (square.piece, square.highlight)
        
        # Clear the board
        for widget in self.board_frame.winfo_children():
            if isinstance(widget, ChessSquare):
                widget.destroy()
            elif isinstance(widget, tk.Label):
                widget.destroy()
        
        # Recreate the squares in flipped orientation
        self.squares = {}
        for row in range(8):
            for col in range(8):
                color = 'light' if (row + col) % 2 == 0 else 'dark'
                # Flipped board: row->7-row
                square = ChessSquare(self.board_frame, self.square_size, row, col, color)
                square.grid(row=7-row, column=7-col)
                square.bind("<Button-1>", lambda e, r=row, c=col: self.on_square_click(r, c))
                self.squares[(row, col)] = square
                
                # Restore the piece and highlight
                if (7-row, 7-col) in current_positions:
                    old_piece, old_highlight = current_positions[(7-row, 7-col)]
                    square.piece = old_piece
                    square.highlight = old_highlight
                    square._draw()
        
        # Add rank and file labels in flipped orientation
        for i in range(8):
            # Rank labels
            tk.Label(self.board_frame, text=str(i+1)).grid(row=7-i, column=8)
            # File labels
            tk.Label(self.board_frame, text=chr(97+i)).grid(row=8, column=7-i)

    def save_comment(self):
        """Save the current comment to the current node."""
        comment = self.comment_text.get(1.0, tk.END).strip()
        self.current_node.comment = comment
        self.update_board()

    def new_game(self):
        """Start a new game."""
        if messagebox.askokcancel("New Game", "Start a new game? Current game will be lost if not saved."):
            self.board.reset()
            self.game = chess.pgn.Game()
            self.current_node = self.game
            self.setup_board()
            self.selected_square = None
            self.legal_moves = []
            self.update_board()

    def load_pgn(self):
        """Load a game from a PGN file."""
        file_path = filedialog.askopenfilename(
            title="Open PGN file",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.game = chess.pgn.read_game(f)
                    if self.game:
                        self.board.reset()
                        self.current_node = self.game
                        
                        # Update headers in the UI
                        if "Event" in self.game.headers:
                            self.event_var.set(self.game.headers["Event"])
                        if "StudyName" in self.game.headers:
                            self.study_var.set(self.game.headers["StudyName"])
                        if "ChapterName" in self.game.headers:
                            self.chapter_var.set(self.game.headers["ChapterName"])
                        
                        self.selected_square = None
                        self.legal_moves = []
                        self.update_board()
                    else:
                        messagebox.showerror("Error", "Failed to load game from PGN file")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading PGN file: {str(e)}")

    def save_pgn(self):
        """Save the current game to a PGN file."""
        file_path = filedialog.asksaveasfilename(
            title="Save PGN file",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            defaultextension=".pgn"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    # Update headers
                    self.game.headers["Event"] = self.event_var.get()
                    self.game.headers["StudyName"] = self.study_var.get()
                    self.game.headers["ChapterName"] = self.chapter_var.get()
                    
                    print(self.game, file=f, end="\n\n")
                messagebox.showinfo("Success", "Game saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving PGN file: {str(e)}")

    def export_chessable(self):
        """Export the game for Chessable using the split_pgn_for_chessable module."""
        if not self.game.variations:
            messagebox.showinfo("Warning", "No moves to export")
            return
            
        # First save the PGN file
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_pgn = os.path.join(temp_dir, "temp_export.pgn")
        
        try:
            with open(temp_pgn, 'w') as f:
                # Update headers
                self.game.headers["Event"] = self.event_var.get()
                self.game.headers["StudyName"] = self.study_var.get()
                self.game.headers["ChapterName"] = self.chapter_var.get()
                
                print(self.game, file=f, end="\n\n")
                
            # Ask for output directory
            output_dir = filedialog.askdirectory(
                title="Select output directory for Chessable PGNs"
            )
            
            if output_dir:
                # Process the PGN file
                process_pgn(temp_pgn, output_dir)
                messagebox.showinfo("Success", f"PGN files exported to {output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting for Chessable: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_pgn):
                os.remove(temp_pgn)

    def find_stockfish(self):
        """Find Stockfish engine on the system."""
        stockfish_paths = []
        
        # Common paths based on OS
        if platform.system() == "Windows":
            stockfish_paths = [
                "stockfish.exe",
                "engines/stockfish.exe",
                "C:/Program Files/stockfish/stockfish.exe",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish.exe")
            ]
        elif platform.system() == "Darwin":  # macOS
            stockfish_paths = [
                "stockfish",
                "/usr/local/bin/stockfish",
                "/opt/homebrew/bin/stockfish",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish")
            ]
        else:  # Linux/Unix
            stockfish_paths = [
                "stockfish",
                "/usr/bin/stockfish", 
                "/usr/local/bin/stockfish",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish")
            ]
        
        # Try to find Stockfish
        for path in stockfish_paths:
            if shutil.which(path) or (os.path.isfile(path) and os.access(path, os.X_OK)):
                self.engine_path = path
                print(f"Found Stockfish at: {path}")
                # Update UI if analysis_button exists
                if hasattr(self, 'analysis_button'):
                    self.analysis_button.config(text="Start Analysis", command=self.start_analysis)
                    
                    # Add the engine line button if it doesn't exist
                    if not hasattr(self, 'engine_line_button'):
                        self.engine_line_button = tk.Button(self.analysis_button.master, text="Add Engine Line")
                        self.engine_line_button.pack(side=tk.LEFT, padx=5)
                        # We'll bind this in the constructor after the add_engine_line method is defined
                break
        
        if self.engine_path is None:
            print("Stockfish not found. Engine analysis will be disabled.")

    def install_stockfish(self):
        """Attempt to install Stockfish engine."""
        if platform.system() == "Darwin":  # macOS
            if messagebox.askyesno("Install Stockfish", 
                                  "Stockfish was not found. Would you like to install it via Homebrew?"):
                try:
                    # Check if Homebrew is installed
                    result = subprocess.run(["which", "brew"], capture_output=True, text=True)
                    if result.returncode != 0:
                        messagebox.showerror("Error", "Homebrew is not installed. Please install Homebrew first.")
                        return
                    
                    # Try to install Stockfish
                    install_cmd = ["brew", "install", "stockfish"]
                    result = subprocess.run(install_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        messagebox.showinfo("Success", "Stockfish installed successfully.")
                        # Find and configure Stockfish
                        self.engine_path = self.find_stockfish_executable()
                        if self.engine_path:
                            # Update the button to show Start Analysis instead of Install
                            self.analysis_button.config(text="Start Analysis", command=self.start_analysis)
                            
                            # Add the engine line button
                            self.engine_line_button = tk.Button(self.analysis_button.master, text="Add Engine Line", command=self.add_engine_line)
                            self.engine_line_button.pack(side=tk.LEFT, padx=5)
                            
                            # Update engine info
                            self.engine_info_var.set(f"Stockfish ready at: {self.engine_path}")
                    else:
                        messagebox.showerror("Error", f"Failed to install Stockfish: {result.stderr}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error during Stockfish installation: {str(e)}")
                    
        elif platform.system() == "Windows":
            messagebox.showinfo("Manual Installation Required", 
                              "Please download Stockfish from https://stockfishchess.org/download/ "
                              "and place the executable in the same folder as this application.")
        else:
            messagebox.showinfo("Manual Installation Required", 
                              "Please install Stockfish using your package manager, e.g., 'sudo apt install stockfish'")

    def find_stockfish_executable(self):
        """Find the Stockfish executable and return its path if found."""
        stockfish_paths = []
        
        # Common paths based on OS
        if platform.system() == "Windows":
            stockfish_paths = [
                "stockfish.exe",
                "engines/stockfish.exe",
                "C:/Program Files/stockfish/stockfish.exe",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish.exe")
            ]
        elif platform.system() == "Darwin":  # macOS
            stockfish_paths = [
                "stockfish",
                "/usr/local/bin/stockfish",
                "/opt/homebrew/bin/stockfish",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish")
            ]
        else:  # Linux/Unix
            stockfish_paths = [
                "stockfish",
                "/usr/bin/stockfish", 
                "/usr/local/bin/stockfish",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish")
            ]
        
        # Try to find Stockfish
        for path in stockfish_paths:
            if shutil.which(path) or (os.path.isfile(path) and os.access(path, os.X_OK)):
                print(f"Found Stockfish at: {path}")
                return path
                
        return None

    def create_engine(self):
        """Create a new engine instance."""
        if self.engine_path:
            try:
                return chess.engine.SimpleEngine.popen_uci(self.engine_path)
            except Exception as e:
                print(f"Error starting Stockfish: {str(e)}")
                return None
        return None
        
    def start_analysis(self):
        """Start engine analysis of the current position."""
        if self.analysis_running:
            return
            
        if not self.engine_path:
            messagebox.showinfo("Engine Not Found", 
                               "Stockfish engine was not found on your system. Please install Stockfish and restart the application.")
            return
            
        # Start analysis in a separate thread to avoid freezing the UI
        self.analysis_running = True
        self.analysis_thread = threading.Thread(target=self.run_analysis)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        # Update UI
        self.analysis_button.config(text="Stop Analysis", command=self.stop_analysis)
        
    def stop_analysis(self):
        """Stop the current engine analysis."""
        if not self.analysis_running:
            return
            
        self.analysis_running = False
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
            self.engine = None
            
        # Update UI
        self.analysis_button.config(text="Start Analysis", command=self.start_analysis)
        self.engine_info_var.set("Analysis stopped")
        
    def run_analysis(self):
        """Run the engine analysis in a background thread."""
        try:
            # Create a new engine instance
            self.engine = self.create_engine()
            if not self.engine:
                self.master.after(0, lambda: self.engine_info_var.set("Failed to start engine"))
                self.analysis_running = False
                return
                
            # Set up analysis parameters
            limit = chess.engine.Limit(time=0.5)  # 500ms per position
            
            # Set timeout of 20 seconds for analysis (adjustable)
            MAX_ANALYSIS_TIME = 20  # seconds
            start_time = datetime.now()
            
            while self.analysis_running:
                # Get current position
                current_pos = self.board.copy()
                
                # Check for timeout
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time > MAX_ANALYSIS_TIME:
                    self.master.after(0, lambda: self.engine_info_var.set("Analysis timeout reached"))
                    self.master.after(0, self.stop_analysis)
                    break
                
                # Run analysis
                with self.engine.analysis(current_pos, limit) as analysis:
                    for info in analysis:
                        if not self.analysis_running:
                            break
                        
                        # Check for timeout during analysis
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        if elapsed_time > MAX_ANALYSIS_TIME:
                            self.master.after(0, lambda: self.engine_info_var.set("Analysis timeout reached"))
                            self.master.after(0, self.stop_analysis)
                            break
                            
                        # Extract evaluation information
                        score_info = ""
                        pv_info = ""
                        depth_info = ""
                        
                        if "score" in info:
                            score = info["score"].relative.score(mate_score=10000)
                            if score is not None:
                                # Convert score to pawns
                                score_pawns = score / 100.0
                                if score_pawns > 0:
                                    score_info = f"+{score_pawns:.2f}"
                                else:
                                    score_info = f"{score_pawns:.2f}"
                            
                            # Check for mate
                            mate = info["score"].relative.mate()
                            if mate is not None:
                                if mate > 0:
                                    score_info = f"M{mate}"
                                else:
                                    score_info = f"M{abs(mate)}"
                        
                        if "depth" in info:
                            depth_info = f"d{info['depth']}"
                            
                        if "pv" in info and len(info["pv"]) > 0:
                            move = info["pv"][0]
                            try:
                                san = current_pos.san(move)
                                pv_info = san
                            except:
                                pv_info = move.uci()
                                
                        # Update the UI
                        engine_text = f"Eval: {score_info} | {depth_info} | Best: {pv_info}"
                        self.master.after(0, lambda t=engine_text: self.engine_info_var.set(t))
                        
                        # If we've reached a good depth, break
                        if "depth" in info and info["depth"] >= 18:
                            break
                            
            # Cleanup
            if self.engine:
                self.engine.quit()
                self.engine = None
                
        except Exception as e:
            print(f"Analysis error: {str(e)}")
        finally:
            self.analysis_running = False
            self.master.after(0, lambda: self.analysis_button.config(text="Start Analysis", command=self.start_analysis))


class VariationTree(tk.Frame):
    """A widget to display and navigate the game tree."""
    def __init__(self, chess_gui, master):
        super().__init__(master)
        self.chess_gui = chess_gui
        self.master = master
        
        # Create a frame for the tree
        tree_frame = tk.LabelFrame(self, text="Moves")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the treeview
        self.tree = ttk.Treeview(tree_frame, selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def update_tree(self, game, current_node):
        """Update the variation tree display."""
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add the game moves to the tree
        self._add_node(game, "", 0, current_node)

    def _add_node(self, node, parent_id, depth, current_node, move_number=1, is_white=True):
        """Recursively add nodes to the tree."""
        if node == current_node:
            tags = ('current',)
        else:
            tags = ()
            
        # Create item text
        text = ""
        if node.parent:
            # This is a move node
            try:
                # Try to get SAN notation safely
                san_move = node.parent.board().san(node.move)
                if is_white:
                    text = f"{move_number}. {san_move}"
                else:
                    text = f"{move_number}... {san_move}"
            except (AssertionError, ValueError) as e:
                # Fallback to UCI notation if SAN fails
                if is_white:
                    text = f"{move_number}. {node.move}"
                else:
                    text = f"{move_number}... {node.move}"
                print(f"Warning: Could not get SAN for move {node.move}: {str(e)}")
                
            # Add comment if exists
            if node.comment:
                comment_preview = node.comment[:20] + "..." if len(node.comment) > 20 else node.comment
                text += f" ({comment_preview})"
        else:
            # This is the root node
            text = "Game Start"
            
        # Add the item to the tree
        item_id = self.tree.insert(parent_id, 'end', text=text, open=True, tags=tags)
        
        # Configure tag for highlighting the current position
        self.tree.tag_configure('current', background='lightblue')
        
        # Add variations
        for i, child in enumerate(node.variations):
            # Update move number and color
            next_move_number = move_number
            next_is_white = not is_white
            if next_is_white:
                next_move_number += 1
                
            self._add_node(child, item_id, depth+1, current_node, next_move_number, next_is_white)

    def on_tree_select(self, event):
        """Handle tree item selection."""
        try:
            # Get the selected item
            selected_item = self.tree.focus()
            if not selected_item:
                return
                
            # Get the item data
            try:
                item_text = self.tree.item(selected_item, "text")
            except _tkinter.TclError:
                # Selected item no longer exists in tree
                return
            
            # Check if it's the root node
            if item_text == "Game Start":
                self.chess_gui.go_to_start()
                return
                
            # First, reset the board
            self.chess_gui.go_to_start()
            
            # Simple approach: just use the display text to navigate
            # Find the move in the text (e.g., "1. e4" -> "e4" or "5... Nf6" -> "Nf6")
            move_text = None
            if "..." in item_text:
                parts = item_text.split("...")
                if len(parts) > 1:
                    move_parts = parts[1].strip().split()
                    if move_parts:
                        move_text = move_parts[0].rstrip('+#').strip()
            elif ". " in item_text:
                parts = item_text.split(". ")
                if len(parts) > 1:
                    move_parts = parts[1].strip().split()
                    if move_parts:
                        move_text = move_parts[0].rstrip('+#').strip()
            
            if not move_text:
                return
                
            # Navigate through the game to find this move
            def find_move_in_game(node, target_text, path=None):
                """Find a move by text recursively through the game tree."""
                if path is None:
                    path = []
                
                for variation in node.variations:
                    try:
                        # Try to get SAN for this move
                        san = node.board().san(variation.move).rstrip('+#')
                        if san == target_text:
                            # Found our move!
                            return path + [variation]
                    except:
                        # If we can't get SAN, try UCI notation
                        if str(variation.move) == target_text:
                            return path + [variation]
                    
                    # Recursively check this variation
                    result = find_move_in_game(variation, target_text, path + [variation])
                    if result:
                        return result
                
                return None
            
            # Find the move in the game tree
            move_path = find_move_in_game(self.chess_gui.game, move_text)
            
            if move_path:
                # Follow the path to the target move
                self.chess_gui.go_to_start()
                for node in move_path:
                    self.chess_gui.board.push(node.move)
                    self.chess_gui.current_node = node
                
                # Update the display
                self.chess_gui.update_board()
            
        except Exception as e:
            print(f"Error in tree selection: {str(e)}")
            # Reset to a safe state
            self.chess_gui.go_to_start()
            self.chess_gui.update_board()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    root.title("Chessable Course Builder")
    root.geometry("1200x800")
    
    # Create and pack the chess board GUI
    chess_gui = ChessboardGUI(root)
    chess_gui.pack(fill=tk.BOTH, expand=True)
    
    # Handle cleanup when the window is closed
    def on_closing():
        if chess_gui.engine:
            chess_gui.stop_analysis()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()


if __name__ == "__main__":
    main()
