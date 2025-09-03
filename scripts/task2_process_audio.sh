#!/bin/bash
# Usage: ./task2_process_audio.sh <input_audio_dir> <output_audio_dir> <num_cpus>

INPUT_DIR=$1
OUTPUT_DIR=$2
N=$3

mkdir -p "$OUTPUT_DIR"

# -----------------------------
# Function to convert audio to WAV, 16kHz, mono
# -----------------------------
convert_file() {
    FILE="$1"
    BASENAME=$(basename "$FILE")
    OUTPUT_FILE="$OUTPUT_DIR/${BASENAME%.*}_16k_mono.wav"
    echo "[INFO] Converting '$FILE' → '$OUTPUT_FILE'"
    ffmpeg -y -i "$FILE" -ar 16000 -ac 1 "$OUTPUT_FILE" -loglevel error
}

export -f convert_file
export OUTPUT_DIR

# -----------------------------
# Step 1: Convert all audio files in parallel
# -----------------------------
echo "[INFO] Starting parallel conversion..."
find "$INPUT_DIR" -type f \( -iname "*.wav" -o -iname "*.mp3" -o -iname "*.m4a" \) -print0 \
    | while IFS= read -r -d '' file; do
        convert_file "$file" &
        while [ "$(jobs -r | wc -l)" -ge "$N" ]; do
            sleep 0.1
        done
      done
wait
echo "[INFO] Parallel conversion complete."

# -----------------------------
# Step 2: Trim trailing silence + last 10s + normalize using Python
# -----------------------------
echo "[INFO] Trimming silence, removing last 10s, and normalizing audio..."

python3 - <<END
import os
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

INPUT_DIR = "$INPUT_DIR"          # Converted audio lives here
TRIMMED_DIR = os.path.join(INPUT_DIR, "trimmed")
os.makedirs(TRIMMED_DIR, exist_ok=True)

files = [f for f in os.listdir(INPUT_DIR) if f.endswith("_16k_mono.wav")]
total = len(files)

for idx, file in enumerate(files, 1):
    input_path = os.path.join(INPUT_DIR, file)
    audio = AudioSegment.from_wav(input_path)

    # Remove last 10 seconds
    duration_ms = len(audio)
    end_trim_ms = max(duration_ms - 10000, 0)
    audio = audio[:end_trim_ms]

    # Detect non-silent parts
    nonsilent = detect_nonsilent(audio, min_silence_len=500, silence_thresh=-40)
    if nonsilent:
        start, end = nonsilent[0][0], nonsilent[-1][1]
        trimmed_audio = audio[start:end]
    else:
        trimmed_audio = audio

    # Normalize volume
    target_dBFS = -20.0
    change_in_dBFS = target_dBFS - trimmed_audio.dBFS
    normalized_audio = trimmed_audio.apply_gain(change_in_dBFS)

    # Export trimmed & normalized audio
    output_path = os.path.join(TRIMMED_DIR, file)
    normalized_audio.export(output_path, format="wav")
    print(f"[INFO] Processed {idx}/{total}: {file} → {output_path}")
END

echo "[DONE] All audio files processed, trimmed (silence + last 10s), and normalized successfully."
