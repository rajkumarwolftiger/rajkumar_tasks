# scripts/task4_create_manifest.py

import os
import json
import soundfile as sf
from tqdm import tqdm # Import tqdm for a nice progress bar

# ---------------------------
# CONFIG (Same format as your original script)
# ---------------------------
# The main input and output directories
AUDIO_DIR = "nptel_data/processed_audio"
TEXT_DIR = "nptel_data/processed_transcripts"
OUTPUT_MANIFEST = "nptel_data/train_manifest.jsonl"

# --- HELPER FUNCTION FOR ROBUST MATCHING ---
def create_file_map(directory: str, extension: str):
    """
    Creates a dictionary mapping a core filename to its full path.
    Example: 'lecture_1_1' -> '/path/to/lecture_1_1.wav'
    """
    file_map = {}
    if not os.path.isdir(directory):
        print(f"[ERROR] Directory not found: {directory}")
        return file_map
        
    for filename in os.listdir(directory):
        if filename.lower().endswith(extension):
            base_name = os.path.splitext(filename)[0]
            full_path = os.path.join(directory, filename)
            file_map[base_name] = full_path
    return file_map

# ---------------------------
# CREATE TRAINING MANIFEST (Main logic block)
# ---------------------------
print("[INFO] Starting manifest creation...")

# Create maps based on core filenames for robust matching.
audio_map = create_file_map(AUDIO_DIR, ".wav")
text_map = create_file_map(TEXT_DIR, ".txt")

# Counters for a better final summary
entry_count = 0
missing_transcript_count = 0

# Open the output file for writing
with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f_out:

    print(f"[INFO] Found {len(audio_map)} audio files. Matching with transcripts...")

    # --- THIS IS THE ONLY CHANGE ---
    # Get the list of core names from the audio files and sort them alphabetically.
    # This will ensure the manifest is written in the correct order (1.1, 1.2, 1.3, etc.).
    sorted_core_names = sorted(audio_map.keys())
    # -------------------------------

    # Iterate through the NEW sorted list of core names
    for core_name in tqdm(sorted_core_names, desc="Creating Manifest"):
        audio_path = audio_map[core_name]
        
        if core_name in text_map:
            text_path = text_map[core_name]

            try:
                # Get duration from the file header instantly with soundfile
                info = sf.info(audio_path)
                duration = round(info.duration, 3)

                # Read transcript
                with open(text_path, "r", encoding="utf-8") as f:
                    transcript = f.read().strip()

                if not transcript:
                    # Don't print a warning inside the tqdm loop to keep output clean
                    continue

                # Create a relative path from the manifest file's location for portability
                manifest_dir = os.path.dirname(os.path.abspath(OUTPUT_MANIFEST))
                relative_audio_path = os.path.relpath(os.path.abspath(audio_path), manifest_dir)

                # Write JSON line
                entry = {
                    "audio_filepath": relative_audio_path,
                    "duration": duration,
                    "text": transcript
                }
                f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                entry_count += 1

            except Exception as e:
                print(f"\n[ERROR] Could not process {os.path.basename(audio_path)}: {e}")

        else:
            missing_transcript_count += 1

# Final Summary
print("\n" + "="*50)
print("MANIFEST CREATION SUMMARY")
print("="*50)
print(f"Total audio files found: {len(audio_map)}")
print(f"Successfully created manifest entries: {entry_count}")
print(f"Audio files with missing transcripts: {missing_transcript_count}")
print(f"\n[DONE] Training manifest created: {OUTPUT_MANIFEST}")
