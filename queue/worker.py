#!/usr/bin/env python
"""
Whisper Queue Worker

Watches the 'inbox' folder for audio files, transcribes them using Whisper,
saves results to 'output', and moves processed files to 'done'.

Usage:
    python queue/worker.py [--model large] [--device cuda:0]
"""

import argparse
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import whisper

# Supported audio extensions
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".webm", ".mp4", ".mpeg", ".mpga"}

# Queue directories (relative to this script's location)
SCRIPT_DIR = Path(__file__).parent
INBOX_DIR = SCRIPT_DIR / "inbox"
OUTPUT_DIR = SCRIPT_DIR / "output"
DONE_DIR = SCRIPT_DIR / "done"
FAILED_DIR = SCRIPT_DIR / "failed"


def setup_directories():
    """Create queue directories if they don't exist."""
    for d in [INBOX_DIR, OUTPUT_DIR, DONE_DIR, FAILED_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def is_file_ready(path: Path, wait_time: float = 1.0) -> bool:
    """Check if a file is fully written (not still being copied)."""
    if not path.exists():
        return False
    try:
        initial_size = path.stat().st_size
        time.sleep(wait_time)
        if not path.exists():
            return False
        return path.stat().st_size == initial_size and initial_size > 0
    except OSError:
        return False


def get_pending_files() -> list[Path]:
    """Get list of audio files waiting in inbox."""
    files = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(INBOX_DIR.glob(f"*{ext}"))
        files.extend(INBOX_DIR.glob(f"*{ext.upper()}"))
    # Filter to files that exist (avoid race conditions)
    files = [f for f in files if f.exists()]
    if not files:
        return []
    return sorted(files, key=lambda f: f.stat().st_mtime)


def transcribe_file(model: whisper.Whisper, audio_path: Path) -> dict:
    """Transcribe a single audio file and return the result."""
    print(f"  Transcribing: {audio_path.name}")
    start = time.time()
    result = model.transcribe(str(audio_path))
    elapsed = time.time() - start
    print(f"  Completed in {elapsed:.1f}s")
    return result


def save_result(audio_path: Path, result: dict):
    """Save transcription result to output folder."""
    output_base = OUTPUT_DIR / audio_path.stem
    
    # Save plain text
    txt_path = output_base.with_suffix(".txt")
    txt_path.write_text(result["text"].strip(), encoding="utf-8")
    
    # Save full JSON with segments and metadata
    json_path = output_base.with_suffix(".json")
    output_data = {
        "text": result["text"],
        "language": result.get("language"),
        "segments": result.get("segments", []),
        "source_file": audio_path.name,
        "processed_at": datetime.now().isoformat(),
    }
    json_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"  Saved: {txt_path.name}, {json_path.name}")


def process_file(model: whisper.Whisper, audio_path: Path):
    """Process a single file: transcribe, save, move to done."""
    # Check file still exists
    if not audio_path.exists():
        print(f"  SKIP: {audio_path.name} no longer exists")
        return
    
    # Wait for file to finish copying
    print(f"  Checking: {audio_path.name}")
    if not is_file_ready(audio_path):
        print(f"  SKIP: {audio_path.name} not ready (still copying?)")
        return
    
    try:
        result = transcribe_file(model, audio_path)
        save_result(audio_path, result)
        # Move to done folder
        if audio_path.exists():
            dest = DONE_DIR / audio_path.name
            shutil.move(str(audio_path), str(dest))
            print("  Moved to done/")
    except Exception as e:
        print(f"  ERROR: {e}")
        # Move to failed folder if file still exists
        if audio_path.exists():
            try:
                dest = FAILED_DIR / audio_path.name
                shutil.move(str(audio_path), str(dest))
                print("  Moved to failed/")
            except Exception as move_err:
                print(f"  Could not move to failed/: {move_err}")


def run_worker(model_name: str = "large", device: str = "cuda:0", poll_interval: float = 2.0):
    """Main worker loop."""
    setup_directories()
    
    print(f"Loading Whisper model '{model_name}' on {device}...")
    model = whisper.load_model(model_name, device=device)
    print("Model loaded. Watching inbox for audio files...\n")
    print(f"  Inbox:  {INBOX_DIR.absolute()}")
    print(f"  Output: {OUTPUT_DIR.absolute()}")
    print(f"  Done:   {DONE_DIR.absolute()}")
    print(f"  Failed: {FAILED_DIR.absolute()}")
    print("\nDrop audio files into inbox/ to transcribe. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            pending = get_pending_files()
            if pending:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(pending)} file(s) to process")
                for audio_path in pending:
                    process_file(model, audio_path)
                print()
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nWorker stopped.")


def main():
    parser = argparse.ArgumentParser(description="Whisper Queue Worker")
    parser.add_argument("--model", default="large", help="Whisper model to use (default: large)")
    parser.add_argument("--device", default="cuda:0", help="Device to run on (default: cuda:0)")
    parser.add_argument("--poll", type=float, default=2.0, help="Poll interval in seconds (default: 2.0)")
    args = parser.parse_args()
    
    run_worker(model_name=args.model, device=args.device, poll_interval=args.poll)


if __name__ == "__main__":
    main()
