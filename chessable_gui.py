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
from PIL import Image, ImageTk
import io
import cairosvg
from datetime import datetime
import re
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
    def __init__(self, master, square_size=64):
        super().__init__(master)
        self.master = master
        self.square_size = square_size
        self.selected_square = None
        self.legal_moves = []
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.current_node = self.game
        self.setup_board()
        self.load_piece_images()
        self.create_board_widgets()
        self.create_control_panel()
        self.variation_tree = VariationTree(self, self.controls_frame)
        self.variation_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.update_board()

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
        
        # Action buttons
        button_frame = tk.Frame(self.controls_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="New Game", command=self.new_game).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Load PGN", command=self.load_pgn).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save PGN", command=self.save_pgn).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Export for Chessable", command=self.export_chessable).pack(side=tk.RIGHT, padx=5)

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
        # Implement board flipping functionality
        pass

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
        selected_item = self.tree.focus()
        if selected_item:
            # Get the path to this node
            path = []
            parent = selected_item
            while parent:
                path.insert(0, parent)
                parent = self.tree.parent(parent)
                
            # Navigate to the selected node
            self.chess_gui.go_to_start()
            
            # Skip the root node
            for i, item_id in enumerate(path):
                if i == 0:
                    continue  # Skip root
                
                try:
                    idx = self.tree.index(item_id)
                    if self.chess_gui.current_node.variations:
                        if idx < len(self.chess_gui.current_node.variations):
                            move = self.chess_gui.current_node.variations[idx].move
                            self.chess_gui.board.push(move)
                            self.chess_gui.current_node = self.chess_gui.current_node.variations[idx]
                except (ValueError, _tkinter.TclError) as e:
                    # Item not found or invalid, skip it
                    print(f"Warning: Error navigating tree at item {item_id}: {str(e)}")
                    continue
                        
            self.chess_gui.update_board()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    root.title("Chessable Course Builder")
    root.geometry("1200x800")
    
    # Create and pack the chess board GUI
    chess_gui = ChessboardGUI(root)
    chess_gui.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()


if __name__ == "__main__":
    main()
