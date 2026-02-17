
import argparse
import os
import sys
import difflib
import re

def normalize_text(text):
    """Normalize text by removing timestamps, whitespace, and punctuation for comparison."""
    # Remove timestamps like [00:12.34]
    text = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', text)
    # Remove whitespace and common punctuation
    text = re.sub(r'[\s\u3000,\.\?!、。？！]', '', text)
    return text

def parse_lrc(lrc_path):
    """Parse LRC file into a list of (timestamp, text) tuples."""
    lines = []
    with open(lrc_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            match = re.match(r'(\[\d{2}:\d{2}\.\d{2}\])(.*)', line)
            if match:
                timestamp = match.group(1)
                content = match.group(2).strip()
                if content: # content might be empty if just checking sync
                    lines.append((timestamp, content))
    return lines

def load_lyrics_text(txt_path):
    """Load original lyric text, ignoring empty lines and section headers like [Chorus]."""
    lines = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignore section headers (e.g. [Aメロ], (間奏)) and empty lines
            if line and not (line.startswith('[') and line.endswith(']')) and not (line.startswith('(') and line.endswith(')')):
                lines.append(line)
    return lines

def main():
    parser = argparse.ArgumentParser(description="Validate LRC file content against original lyrics text.")
    parser.add_argument("lrc_path", help="Path to the generated LRC file")
    parser.add_argument("lyrics_path", help="Path to the original lyrics text file")

    args = parser.parse_args()

    if not os.path.exists(args.lrc_path):
        print(f"Error: LRC file not found: {args.lrc_path}")
        sys.exit(1)
    
    if not os.path.exists(args.lyrics_path):
        print(f"Error: Lyrics file not found: {args.lyrics_path}")
        sys.exit(1)

    print(f"Validating {os.path.basename(args.lrc_path)} against {os.path.basename(args.lyrics_path)}...\n")

    lrc_data = parse_lrc(args.lrc_path)
    lrc_lines = [content for _, content in lrc_data]
    
    original_lines = load_lyrics_text(args.lyrics_path)

    # Simple normalization for comparison
    normalized_lrc = [normalize_text(line) for line in lrc_lines]
    normalized_original = [normalize_text(line) for line in original_lines]

    # Join them to compare the full content flow
    lrc_full_text = "".join(normalized_lrc)
    original_full_text = "".join(normalized_original)
    
    has_error = False

    if lrc_full_text == original_full_text:
        print("✅ Success! The LRC content matches the original lyrics perfectly (ignoring whitespace/punctuation).")
    else:
        print("⚠️  Mismatch detected between LRC and Original Lyrics!")
        has_error = True
        
        # Show diff on line-by-line basis if counts match, otherwise just diff the block?
        # Let's try to match lines first.
        
        matcher = difflib.SequenceMatcher(None, lrc_lines, original_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                print(f"\n[Mismatch]")
                for i in range(i1, i2):
                    print(f"  LRC ({lrc_data[i][0]}): {lrc_lines[i]}")
                print(f"  --- vs ---")
                for j in range(j1, j2):
                    print(f"  ORIGINAL: {original_lines[j]}")
            elif tag == 'delete':
                print(f"\n[Extra lines in LRC]")
                for i in range(i1, i2):
                    print(f"  LRC ({lrc_data[i][0]}): {lrc_lines[i]}")
            elif tag == 'insert':
                print(f"\n[Missing lines in LRC]")
                for j in range(j1, j2):
                    print(f"  ORIGINAL: {original_lines[j]}")
    
    # Check if number of lines is significantly different
    if abs(len(lrc_lines) - len(original_lines)) > 0:
        print(f"\n[Line Count Warning] LRC has {len(lrc_lines)} lines, Original has {len(original_lines)} lines.")
        if not has_error:
             print("Text content matched after normalization, but line breaks might be different.")

    if has_error:
        print("\nNote: Please edit the LRC file manually to fix these discrepancies before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
