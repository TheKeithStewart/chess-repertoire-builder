#!/usr/bin/env python3
"""
Lichess to Chessable PGN Converter

This script splits a Lichess PGN study into separate PGN files for Chessable,
with each top-level variation becoming its own chapter.
"""

import re
import os
import sys
import chess.pgn
from io import StringIO
import argparse
from datetime import datetime


def extract_metadata(pgn_content):
    """Extract metadata from PGN content."""
    metadata = {}
    pattern = r'\[(.*?) "(.*?)"\]'
    matches = re.findall(pattern, pgn_content)
    
    for tag, value in matches:
        metadata[tag] = value
    
    return metadata


def create_chapter_name(variation_comment):
    """Create a chapter name from the variation comment."""
    if not variation_comment:
        return "Main Line"
    
    # Extract opening name from comment if available
    comment_text = variation_comment.strip()
    return comment_text


def process_pgn(input_file, output_dir):
    """Process the input PGN file and create separate chapters."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read the input PGN file
    with open(input_file, 'r', encoding='utf-8') as f:
        pgn_content = f.read()
    
    # Look for special split marker in comments
    SPLIT_MARKER = "[SPLIT_CHAPTERS]"
    has_split_marker = SPLIT_MARKER in pgn_content
    
    # Extract metadata
    metadata = extract_metadata(pgn_content)
    study_name = metadata.get('StudyName', 'Untitled Study')
    chapter_name = metadata.get('ChapterName', 'Untitled Chapter')
    
    # Parse the PGN
    pgn = StringIO(pgn_content)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        print("Error: Could not parse PGN file.")
        return

    # Get the main line
    main_line = game.mainline_moves()
    main_line_str = ' '.join([move.uci() for move in main_line])
    
    # Find the node where we should split chapters
    split_node = find_split_node(game, SPLIT_MARKER) if has_split_marker else None
    
    # Initialize current_node variable 
    current_node = None
    
    if split_node:
        print(f"Found split marker - splitting chapters at the marked position")
        node = split_node
    else:
        # For Lichess PGNs, look for the position where variations appear as alternatives
    # to moves in the main line (these appear in parentheses in the PGN)
        node = game
        current_node = game
        found_split_point = False
        
        # First try to find nodes that have siblings - this indicates variation branches
        # in the Lichess PGN format (parenthesized variations)
        stack = [game]
        main_line_nodes = []
        
        # First collect all main line nodes
        temp_node = game
        while temp_node.variations:
            main_line_nodes.append(temp_node)
            temp_node = temp_node.variations[0]
        main_line_nodes.append(temp_node)  # Add the last node
        
        # Now look for the first node that has alternatives/siblings
        for n in main_line_nodes:
            if n.variations and len(n.variations) > 0:
                variations_at_node = []
                
                # Skip the first variation (main line) and collect siblings
                for i in range(1, len(n.variations)):
                    variations_at_node.append(n.variations[i])
                
                # If we found variations at this node, we've found our split point
                if variations_at_node:
                    node = n
                    found_split_point = True
                    print(f"Found split point at move: {n.board().fullmove_number}")
                    break
        
        # Fallback to looking for branches in the main line
        if not found_split_point:
            while current_node.variations:
                current_node = current_node.variations[0]  # Follow the main line
                
                # Check if this position has variations
                if len(current_node.variations) > 0:
                    node = current_node
                    break
    
    # Collect the variations to process - for Lichess PGNs, we want the main line plus siblings
    all_variations = []
    
    # Add the main line first
    if node.variations:
        all_variations.append(node.variations[0])  # Main line continuation
    
    # Then add all alternative variations (siblings to the main line)
    if node.variations and len(node.variations) > 1:
        for i in range(1, len(node.variations)):
            all_variations.append(node.variations[i])
    
    if not all_variations:
        print("No variations found to split into chapters.")
        output_file = os.path.join(output_dir, "main_line.pgn")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pgn_content)
        print(f"Saved main line to {output_file}")
        return
    
    # Process each variation including the main line
    for i, variation in enumerate(all_variations):
        # For the main line (first variation)
        if i == 0:
            comment = variation.comment.strip() if variation.comment else "Main Line"
            if "Main Line" in comment:
                variation_name = comment
            else:
                variation_name = "Main Line - " + (comment or metadata.get('Opening', 'Opening'))
        else:
            # Get the variation comment from the move
            comment = variation.comment.strip() if variation.comment else f"Variation {i}"
            variation_name = create_chapter_name(comment)
        
        # Create a new game for this variation
        new_game = chess.pgn.Game()
        
        # Copy all headers from the original game
        for key, value in game.headers.items():
            new_game.headers[key] = value
        
        # Update chapter name
        new_game.headers["ChapterName"] = f"{chapter_name}: {variation_name}"
        
        # Create date for the new PGN
        today = datetime.now().strftime("%Y.%m.%d")
        new_game.headers["UTCDate"] = today
        
        # Build the new game's moves
        # First, add the moves leading up to the variation point
        parent = variation.parent
        move_stack = []
        while parent.parent:
            move_stack.append(parent.move)
            parent = parent.parent
        move_stack.reverse()
        
        # Create the root node for our new game
        new_node = new_game
        
        # Add the moves leading to the variation
        for move in move_stack:
            new_node = new_node.add_variation(move)
        
        # Add the variation move and all subsequent moves
        new_node = new_node.add_variation(variation.move)
        new_node.comment = variation.comment
        
        # Add all moves in this variation
        curr_var_node = variation.variations[0] if variation.variations else None
        while curr_var_node:
            new_node = new_node.add_variation(curr_var_node.move)
            new_node.comment = curr_var_node.comment
            
            # Also add any subvariations
            for subvar in curr_var_node.variations[1:]:
                add_variation_recursively(new_node, subvar)
                
            curr_var_node = curr_var_node.variations[0] if curr_var_node.variations else None
        
        # Add all annotations and NAGs
        copy_annotations(game, new_game)
        
        # Write to file
        safe_name = re.sub(r'[^\w\s-]', '', variation_name).strip().replace(' ', '_')
        output_file = os.path.join(output_dir, f"{i:02d}_{safe_name}.pgn")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            exporter = chess.pgn.FileExporter(f)
            new_game.accept(exporter)
        
        print(f"Created chapter: {variation_name} -> {output_file}")


def find_split_node(game, marker):
    """Find a node with the split marker in its comment."""
    stack = [game]
    
    while stack:
        node = stack.pop()
        
        # Check if this node contains the marker
        if node.comment and marker in node.comment:
            # Remove the marker from the comment
            node.comment = node.comment.replace(marker, "").strip()
            return node
        
        # Add child nodes to the stack in reverse order
        # (so we process them in the correct order)
        for child in reversed(node.variations):
            stack.append(child)
    
    return None


def add_variation_recursively(parent_node, variation_node):
    """Recursively add all subvariations."""
    new_node = parent_node.add_variation(variation_node.move)
    new_node.comment = variation_node.comment
    
    for nag in variation_node.nags:
        new_node.nags.add(nag)
    
    for child in variation_node.variations:
        add_variation_recursively(new_node, child)


def copy_annotations(src_game, dst_game):
    """Copy annotations from source game to destination game."""
    # This is a simplified version - in a complete implementation,
    # you would recursively walk both trees and copy annotations
    # For now, we just copy game-level comments
    dst_game.comment = src_game.comment


def main():
    parser = argparse.ArgumentParser(description="Split Lichess PGN into Chessable chapters")
    parser.add_argument("input", help="Input PGN file from Lichess")
    parser.add_argument("-o", "--output-dir", default="output",
                        help="Output directory for chapter PGNs (default: 'output')")
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return 1
    
    process_pgn(args.input, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
