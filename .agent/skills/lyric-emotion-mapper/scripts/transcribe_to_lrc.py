
import argparse
import os
import sys
import math
import time
from faster_whisper import WhisperModel
from tqdm import tqdm
import subprocess

def get_audio_duration(file_path):
    """Get audio duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not determine audio duration for progress bar: {e}")
        return None

def format_lrc_timestamp(seconds):
    """Format seconds to [mm:ss.xx] for LRC."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"[{m:02d}:{s:02d}.{cs:02d}]"

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio to LRC using faster-whisper.")
    parser.add_argument("audio_path", help="Path to the input audio file")
    parser.add_argument("--lyrics", help="Path to text file containing lyrics (for prompting/context)", default=None)
    parser.add_argument("--output", help="Path to output LRC file", default=None)
    parser.add_argument("--model", help="Whisper model size", default="small")
    parser.add_argument("--language", help="Language code", default="ja")
    parser.add_argument("--device", help="Device to use (cuda or cpu)", default="cpu") # Default to cpu for mac compat usually, or auto

    args = parser.parse_args()

    if not os.path.exists(args.audio_path):
        print(f"Error: Audio file not found: {args.audio_path}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.splitext(args.audio_path)[0] + ".lrc"

    # Prepare initial prompt from lyrics file if provided
    initial_prompt = None
    if args.lyrics and os.path.exists(args.lyrics):
        with open(args.lyrics, "r", encoding="utf-8") as f:
            initial_prompt = f.read()
        print(f"Loaded lyrics for context prompt from: {args.lyrics}")

    print(f"Loading Whisper model ({args.model})...")
    # On macOS with Apple Silicon, 'cpu' with INT8 is often default/fast enough, or 'cuda' if user has nvidia. 
    # For CoreML/MPS support with faster-whisper, it's limited. CPU is safest default output.
    # The user might have a specific setup, but basic load:
    try:
        model = WhisperModel(args.model, device=args.device, compute_type="int8")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    duration = get_audio_duration(args.audio_path)
    
    print(f"Starting transcription for: {args.audio_path}")
    print(f"Output will be saved to: {output_path}")

    segments, info = model.transcribe(
        args.audio_path, 
        language=args.language, 
        initial_prompt=initial_prompt,
        word_timestamps=False
    )

    # Prepare progress bar
    pbar = tqdm(total=duration, unit="sec", bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]") if duration else None

    lrc_lines = []
    
    current_time = 0
    for segment in segments:
        start_time = segment.start
        end_time = segment.end
        text = segment.text.strip()

        lrc_line = f"{format_lrc_timestamp(start_time)}{text}"
        lrc_lines.append(lrc_line)
        
        if pbar:
            pbar.update(end_time - current_time)
            current_time = end_time

    if pbar:
        pbar.close()

    # Write LRC file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lrc_lines))

    print(f"\nSuccess! LRC file created at: {output_path}")

if __name__ == "__main__":
    main()
