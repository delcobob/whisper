# Whisper Queue System

A simple folder-based queue for batch transcription with Whisper.

## Folder Structure

```
queue/
├── inbox/      # Drop audio files here
├── output/     # Transcription results (.txt and .json)
├── done/       # Processed audio files
├── failed/     # Files that failed to process
├── worker.py   # The worker script
├── enqueue.py  # Helper to add files to queue
└── README.md
```

## Usage

### 1. Start the worker

```powershell
.venv\Scripts\python queue\worker.py
```

Options:
- `--model large` - Whisper model (default: large)
- `--device cuda:0` - GPU device (default: cuda:0)
- `--poll 2.0` - Poll interval in seconds

### 2. Add files to the queue

**Option A:** Use the enqueue script:
```powershell
.venv\Scripts\python queue\enqueue.py path\to\audio.mp3 another.wav
```

**Option B:** Just copy/drag files directly into `queue/inbox/`

### 3. Get results

Transcriptions appear in `queue/output/`:
- `filename.txt` - Plain text transcription
- `filename.json` - Full result with segments and timestamps

## Supported Formats

MP3, WAV, FLAC, M4A, OGG, WEBM, MP4, MPEG, MPGA

## Example Session

```powershell
# Terminal 1: Start worker
.venv\Scripts\python queue\worker.py --model large --device cuda:0

# Terminal 2: Add files
.venv\Scripts\python queue\enqueue.py C:\recordings\*.mp3
```

The worker will process files in order and keep watching for new ones.
