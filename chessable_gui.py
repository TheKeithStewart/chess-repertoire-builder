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
        self.board_flipped = False  # Track board orientation
        self.setup_board()
        self.load_piece_images()
        self.create_board_widgets()
        self.create_control_panel()
        
        # Create variation tree for moves
        self.variation_tree = VariationTree(self, self.controls_frame)
        self.variation_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a status bar
        self.status_var = tk.StringVar(value="Ready. Shortcuts: ← → (navigate), Home/End (start/end), F (flip board), E (analysis)")
        self.status_bar = tk.Label(self.controls_frame, textvariable=self.status_var, 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=5, pady=2)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
        
        self.create_squares()
        self.create_board_labels()
                
    def create_squares(self):
        """Create the chess board squares based on current orientation."""
        self.squares = {}
        for row in range(8):
            for col in range(8):
                # Determine square color (light or dark)
                color = 'light' if (row + col) % 2 == 0 else 'dark'
                
                # Calculate display positions based on board orientation
                if self.board_flipped:
                    display_row, display_col = row, 7 - col
                    chess_row, chess_col = row, col
                else:
                    display_row, display_col = row, col
                    chess_row, chess_col = 7 - row, col
                
                # Create the square
                square = ChessSquare(self.board_frame, self.square_size, chess_row, chess_col, color)
                square.grid(row=display_row, column=display_col)
                
                # Bind click event - pass the chess coordinate (not display coordinate)
                square.bind("<Button-1>", lambda e, r=chess_row, c=chess_col: self.on_square_click(r, c))
                
                # Store the square with its chess coordinates (not display coordinates)
                self.squares[(chess_row, chess_col)] = square
    
    def create_board_labels(self):
        """Create the rank and file labels based on current orientation."""
        # Remove any existing labels
        for widget in self.board_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.destroy()
                
        # Add rank and file labels
        for i in range(8):
            # Rank labels (1-8)
            tk.Label(self.board_frame, text=str(i+1)).grid(row=7-i, column=8)
            
            # File labels (a-h)
            if self.board_flipped:
                file_col = 7 - i  # Reversed when flipped
            else:
                file_col = i
            tk.Label(self.board_frame, text=chr(97+i)).grid(row=8, column=file_col)

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
        try:
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
                
            # Update variation tree with the current position
            self.variation_tree.update_tree(self.game, self.current_node)
            
            # Update engine analysis if running
            if self.analysis_running:
                # We don't need to restart the analysis as it continuously evaluates the current position
                pass
            else:
                # Clear engine info
                self.engine_info_var.set("Engine not running")
                
            # Update status bar with current position info
            turn = "White" if self.board.turn == chess.WHITE else "Black"
            move_number = (self.board.fullmove_number if self.board.turn == chess.BLACK 
                           else self.board.fullmove_number)
            status_text = f"{turn} to move. Move: {move_number}. "
            
            # Add evaluation if available
            if self.analysis_running and hasattr(self, 'engine_info_var'):
                engine_info = self.engine_info_var.get()
                if "Score:" in engine_info:
                    status_text += f"{engine_info.split('Score:')[1].strip().split()[0]} "
                    
            # Add keyboard shortcuts reminder
            status_text += "| ← → (navigate), Home/End, F (flip), E (analysis)"
            self.status_var.set(status_text)
            
        except Exception as e:
            print(f"Error updating board: {str(e)}")
            self.status_var.set(f"Error updating display. See console for details.")

    def on_square_click(self, row, col):
        """Handle clicks on the chess board squares."""
        square = chess.square(col, row)
        square_name = chess.square_name(square)
        
        if self.selected_square:
            # Check if this is a legal target square
            from_square = chess.square(self.selected_square[1], self.selected_square[0])
            from_square_name = chess.square_name(from_square)
            move = chess.Move(from_square, square)
            
            # Update status bar
            self.status_var.set(f"Selected move: {from_square_name} to {square_name}")
            
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
        # Toggle the flipped state
        self.board_flipped = not self.board_flipped
        
        # Clear the existing squares
        for widget in self.board_frame.winfo_children():
            if isinstance(widget, ChessSquare):
                widget.destroy()
        
        # Recreate the squares and labels with the new orientation
        self.create_squares()
        self.create_board_labels()
        
        # Update the board with the current position
        self.update_board()

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
        self.engine_info_var.set("Starting analysis...")
        
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
        
        # Only update the info if it's not already showing a result
        current_info = self.engine_info_var.get()
        if not "Eval:" in current_info and not "Analysis completed" in current_info:
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
            
            # Set timeout of 10 seconds for analysis (adjustable)
            MAX_ANALYSIS_TIME = 10  # seconds
            start_time = datetime.now()
            last_result = None
            
            while self.analysis_running:
                # Get current position
                current_pos = self.board.copy()
                
                # Check for timeout
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time > MAX_ANALYSIS_TIME:
                    if last_result:
                        self.master.after(0, lambda: self.engine_info_var.set(f"{last_result} (Analysis completed)"))
                    else:
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
                            if last_result:
                                self.master.after(0, lambda: self.engine_info_var.set(f"{last_result} (Analysis completed)"))
                            else:
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
                        last_result = engine_text
                        
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


class MoveButton(tk.Button):
    """A button representing a chess move."""
    def __init__(self, master, text, move_node=None, comment="", is_current=False, **kwargs):
        # Create a custom style for the button
        super().__init__(
            master, 
            text=text, 
            padx=2, 
            pady=1, 
            relief=tk.GROOVE,
            bg="lightblue" if is_current else "#f0f0f0",
            activebackground="#d0d0ff" if is_current else "#e0e0e0",
            borderwidth=1,
            **kwargs
        )
        self.move_node = move_node
        self.comment = comment
        self.is_current = is_current
        
    def set_current(self, is_current):
        """Set whether this move is the current position."""
        self.is_current = is_current
        self.config(bg="lightblue" if is_current else "#f0f0f0")
        self.config(activebackground="#d0d0ff" if is_current else "#e0e0e0")


class VariationTree(tk.Frame):
    """A widget to display and navigate the game tree."""
    def __init__(self, chess_gui, master):
        super().__init__(master)
        self.chess_gui = chess_gui
        self.master = master
        
        # Create a frame for the moves with a label and filter
        moves_header_frame = tk.Frame(self)
        moves_header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.moves_label = tk.Label(moves_header_frame, text="Moves", font=("TkDefaultFont", 10, "bold"))
        self.moves_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Add a search/filter box
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._filter_changed)  # Using trace_add instead of trace
        filter_entry = tk.Entry(moves_header_frame, textvariable=self.filter_var, width=15)
        filter_entry.pack(side=tk.RIGHT, padx=(5, 0))
        
        filter_label = tk.Label(moves_header_frame, text="Filter:")
        filter_label.pack(side=tk.RIGHT)
        
        # Create a frame to hold the moves
        self.moves_container = tk.Frame(self, bd=1, relief=tk.SUNKEN)
        self.moves_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a canvas with scrolling capability
        self.canvas = tk.Canvas(self.moves_container, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.moves_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas to hold the moves content
        self.moves_frame = tk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.moves_frame, anchor="nw")
        
        # Configure canvas to adjust with frame size
        self.moves_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # List to keep track of created move buttons and search ability
        self.move_buttons = []
        self.current_game = None
        self.current_position = None
        
        # Add mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
    
    def _filter_changed(self, *args):
        """Handle filter text changes"""
        if self.current_game and self.current_position:
            self.update_tree(self.current_game, self.current_position)

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """When the canvas changes size, resize the frame within it."""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        # Cross-platform mouse wheel scrolling
        try:
            if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
                self.canvas.yview_scroll(1, "units")
            # For macOS
            elif hasattr(event, 'delta'):
                if event.delta < 0:
                    self.canvas.yview_scroll(1, "units")
                else:
                    self.canvas.yview_scroll(-1, "units")
        except Exception as e:
            # Fallback for any platform-specific issues
            print(f"Mouse wheel error: {str(e)}")

    def update_tree(self, game, current_node):
        """Update the move display with the current game tree."""
        # Store current game and position for filter usage
        self.current_game = game
        self.current_position = current_node
        
        # Get filter text
        filter_text = self.filter_var.get().lower()
        
        # Clear existing moves
        for widget in self.moves_frame.winfo_children():
            widget.destroy()
        self.move_buttons = []
        
        # Add a "Start" button to return to initial position
        start_btn = MoveButton(
            self.moves_frame, 
            text="Start", 
            is_current=(current_node == game),
            command=lambda: self.chess_gui.go_to_start()
        )
        start_btn.grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.move_buttons.append((game, start_btn))
        
        # Build the tree of moves
        row = self._build_variation(game, current_node, row=1, variation_level=0, filter_text=filter_text)
        
        # If no moves were shown due to filtering, add a message
        if row == 1 and filter_text:
            no_results = tk.Label(self.moves_frame, text=f"No moves match '{filter_text}'")
            no_results.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        # Update the scrollbar
        self.moves_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Ensure current move is visible
        self._scroll_to_current_move()

    def _build_variation(self, node, current_node, row, variation_level=0, move_number=1, is_white=True, filter_text=""):
        """Build a variation starting from the given node."""
        # Skip the root node, go straight to its variations
        if node == self.chess_gui.game:
            for i, variation in enumerate(node.variations):
                next_row = self._build_variation(
                    variation, current_node, row, 
                    variation_level, move_number, is_white,
                    filter_text
                )
                row = next_row
            return row
        
        # Get move in SAN notation
        try:
            san = node.parent.board().san(node.move)
        except (AssertionError, ValueError):
            san = str(node.move)
        
        # Get comment (if any)
        comment = node.comment if node.comment else ""
        
        # Check if this move matches the filter
        match_filter = (
            not filter_text or 
            filter_text.lower() in san.lower() or 
            (comment and filter_text.lower() in comment.lower())
        )
        
        # Skip rendering this move and its variations if it doesn't match the filter
        # Unless it's on the path to the current position
        is_current = (node == current_node)
        is_on_path_to_current = is_current
        
        if not is_current and current_node != self.chess_gui.game:
            # Check if this node is on the path to the current position
            temp_node = current_node
            while temp_node != self.chess_gui.game:
                if temp_node == node:
                    is_on_path_to_current = True
                    break
                temp_node = temp_node.parent
        
        # Skip if doesn't match filter and not on path to current move
        if not match_filter and not is_on_path_to_current:
            return row
        
        # Calculate the column based on whether it's a white or black move
        base_col = variation_level * 3  # Each variation level gets 3 columns (number, white, black)
        
        if is_white:
            # Add move number in the first column of this variation level
            num_label = tk.Label(
                self.moves_frame, 
                text=f"{move_number}.", 
                padx=2, 
                pady=1
            )
            num_label.grid(row=row, column=base_col, sticky="e")
            
            # Column for white's move is base_col + 1
            move_col = base_col + 1
            next_is_white = False
            next_move_number = move_number
        else:
            # Column for black's move is base_col + 2
            move_col = base_col + 2
            next_is_white = True
            next_move_number = move_number + 1
        
        # Create the move button
        move_btn = MoveButton(
            self.moves_frame,
            text=san,
            move_node=node,
            comment=comment,
            is_current=is_current,
            command=lambda n=node: self._go_to_node(n)
        )
        move_btn.grid(row=row, column=move_col, sticky="w", padx=2, pady=1)
        
        # Add tooltip with comment if present
        if comment:
            self._create_tooltip(move_btn, comment)
        
        # Keep track of this button
        self.move_buttons.append((node, move_btn))
        
        # Process mainline continuation
        if node.variations:
            main_variation = node.variations[0]
            next_row = self._build_variation(
                main_variation, current_node, row if not next_is_white else row+1,
                variation_level, next_move_number, next_is_white, filter_text
            )
            row = next_row
        else:
            # If this move has no continuation, the next row is the next one
            row += 1 if is_white else 1
        
        # Process alternative variations (sidelines)
        for i in range(1, len(node.variations)):
            variation = node.variations[i]
            
            # Add a new row and increase the variation level for alternative lines
            row += 1
            next_row = self._build_variation(
                variation, current_node, row,
                variation_level + 1, move_number, is_white, filter_text
            )
            row = next_row
            
        return row

    def _go_to_node(self, target_node):
        """Navigate to the specified node in the game tree."""
        try:
            # Find path from root to target node
            path = []
            current = target_node
            while current != self.chess_gui.game:
                path.insert(0, current)
                current = current.parent
                
            # Reset to start position
            self.chess_gui.go_to_start()
            
            # Follow path to target node
            for node in path:
                self.chess_gui.board.push(node.move)
                self.chess_gui.current_node = node
                
            # Update the board display
            self.chess_gui.update_board()
            
        except Exception as e:
            print(f"Error navigating to node: {str(e)}")
            # Reset to a safe state
            self.chess_gui.go_to_start()
            self.chess_gui.update_board()
    
    def _scroll_to_current_move(self):
        """Ensure the current move is visible in the scrolled area."""
        for node, btn in self.move_buttons:
            if btn.is_current:
                # Get button position
                x, y = btn.winfo_x(), btn.winfo_y()
                
                # Calculate canvas scrolling
                canvas_height = self.canvas.winfo_height()
                
                # Scroll so the button is in the middle
                self.canvas.yview_moveto(max(0, (y - canvas_height/2) / self.moves_frame.winfo_height()))
                break
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a top-level window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, justify='left',
                            background="#ffffff", relief="solid", borderwidth=1,
                            padx=4, pady=2, wraplength=300)
            label.pack()
            
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    root.title("Chessable Course Builder")
    root.geometry("1200x800")
    
    # Set up keyboard shortcuts
    def setup_keyboard_shortcuts(app):
        # Navigation shortcuts
        root.bind('<Left>', lambda e: app.go_back())
        root.bind('<Right>', lambda e: app.go_forward())
        root.bind('<Home>', lambda e: app.go_to_start())
        root.bind('<End>', lambda e: app.go_to_end())
        # Flip board
        root.bind('<F>', lambda e: app.flip_board())
        # Engine analysis
        root.bind('<E>', lambda e: app.start_analysis() if hasattr(app, 'analysis_running') and not app.analysis_running else None)
    
    # Create and pack the chess board GUI
    chess_gui = ChessboardGUI(root)
    chess_gui.pack(fill=tk.BOTH, expand=True)
    
    # Set up the keyboard shortcuts
    setup_keyboard_shortcuts(chess_gui)
    
    # Handle cleanup when the window is closed
    def on_closing():
        if chess_gui.engine:
            chess_gui.stop_analysis()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()


if __name__ == "__main__":
    main()
