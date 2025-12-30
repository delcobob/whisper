#!/usr/bin/env python
"""
Enqueue audio files for Whisper transcription.

Usage:
    python queue/enqueue.py file1.mp3 file2.wav ...
    python queue/enqueue.py *.mp3
"""

import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
INBOX_DIR = SCRIPT_DIR / "inbox"


def enqueue_files(file_paths: list[str]):
    """Copy files to the inbox folder."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    
    for file_path in file_paths:
        src = Path(file_path)
        if not src.exists():
            print(f"File not found: {src}")
            continue
        if not src.is_file():
            print(f"Not a file: {src}")
            continue
        
        dest = INBOX_DIR / src.name
        if dest.exists():
            print(f"Already in queue: {src.name}")
            continue
        
        shutil.copy2(str(src), str(dest))
        print(f"Queued: {src.name}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python enqueue.py <audio_file> [audio_file ...]")
        print("\nExample:")
        print("  python queue/enqueue.py interview.mp3 podcast.wav")
        sys.exit(1)
    
    enqueue_files(sys.argv[1:])
    print("\nFiles will be processed by worker. Run:")
    print("  python queue/worker.py")


if __name__ == "__main__":
    main()
