#!/usr/bin/env python3
"""
Script to edit video:
1. Trim to 20 seconds (at normal speed)
2. Speed up remaining video by 1.5X
3. Save as sovereign_consumer_prototype.mov
"""

import subprocess
import os
import glob
from pathlib import Path

def edit_video():
    # Find the input file dynamically
    script_dir = Path(__file__).parent
    mov_files = list(script_dir.glob("Screen Recording*.mov"))
    
    if not mov_files:
        print("Error: No 'Screen Recording*.mov' file found!")
        return False
    
    input_file = str(mov_files[0])
    output_file = "sovereign_consumer_prototype.mov"
    
    print(f"Found input file: {input_file}")
    
    # FFmpeg command:
    # -i: input file
    # -t 20: trim to 20 seconds
    # -filter:v "setpts=0.666*PTS": speed up video by 1.5x (1/1.5 = 0.666)
    # -filter:a "atempo=1.5": speed up audio by 1.5x
    # -c:v libx264: video codec
    # -c:a aac: audio codec
    # -y: overwrite output file if it exists
    
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-t", "20",  # Trim to 20 seconds
        "-filter:v", "setpts=0.666*PTS",  # Speed up video 1.5x
        "-filter:a", "atempo=1.5",  # Speed up audio 1.5x
        "-c:v", "libx264",
        "-c:a", "aac",
        "-y",  # Overwrite output if exists
        output_file
    ]
    
    print(f"Processing video: {input_file}")
    print(f"Output file: {output_file}")
    print("\nRunning ffmpeg command...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n✓ Video processing completed successfully!")
        print(f"✓ Output saved as: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error processing video:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("\n✗ Error: ffmpeg not found!")
        print("Please install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        return False

if __name__ == "__main__":
    edit_video()
