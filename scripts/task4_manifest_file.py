import os
import glob
import json
from pydub import AudioSegment

# ---------------------------
# CONFIG
# ---------------------------
AUDIO_DIR = "nptel_data/processed_audio/trimmed"  # Where trimmed audio is stored
TEXT_DIR = "nptel_data/processed_transcripts"           # Where processed transcripts are stored
OUTPUT_MANIFEST = "nptel_data/train_manifest.jsonl"

# ---------------------------
# CREATE TRAINING MANIFEST
# ---------------------------
with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f_out:
    audio_files = glob.glob(os.path.join(AUDIO_DIR, "*.wav"))
    audio_files.sort()  # Optional: sort to match transcripts

    for audio_file in audio_files:
        # Corresponding text file
        base_name = os.path.basename(audio_file).replace("_16k_mono.wav", ".txt")
        text_file = os.path.join(TEXT_DIR, base_name)

        if not os.path.exists(text_file):
            print(f"[WARNING] Transcript missing for {audio_file}, skipping...")
            continue

        # Read transcript
        with open(text_file, "r", encoding="utf-8") as f:
            transcript = f.read().strip()

        if not transcript:
            print(f"[WARNING] Empty transcript for {audio_file}, skipping...")
            continue

        # Get duration in seconds
        audio = AudioSegment.from_wav(audio_file)
        duration = round(len(audio) / 1000.0, 2)  # milliseconds → seconds

        # Write JSON line
        entry = {
            "audio_filepath": audio_file,
            "duration": duration,
            "text": transcript
        }
        f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Added {audio_file} → {OUTPUT_MANIFEST}")

print(f"\n[DONE] Training manifest created: {OUTPUT_MANIFEST}")
