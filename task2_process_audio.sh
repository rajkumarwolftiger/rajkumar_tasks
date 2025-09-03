#!/bin/bash
# Usage: ./task2_process_audio.sh <input_dir> <output_dir> <num_cpus>
# Example: bash task2_process_audio.sh nptel_data/audio/ nptel_data/processed_audio/ 4
#
# This version has the trim times (12s start, 31s end) hardcoded.

# --- VALIDATE INPUTS ---
if [ "$#" -ne 3 ]; then
    echo "ERROR: Invalid number of arguments."
    echo "Usage: $0 <input_dir> <output_dir> <num_cpus>"
    exit 1
fi

INPUT_DIR=$1
OUTPUT_DIR=$2
N=$3

# --- HARDCODED TRIM TIMES ---
# CHANGED: The trim durations are now fixed inside the script.
START_TRIM=12
END_TRIM=30
# ---------------------------

# --- SETUP ---
mkdir -p "$OUTPUT_DIR"

# --- WORKER FUNCTION ---
process_one_file() {
    local input_file="$1"
    local output_dir="$2"
    local start_trim="$3"
    local end_trim="$4"

    if [ ! -f "$input_file" ]; then
        return 1
    fi

    local base_name
    base_name=$(basename "$input_file")
    local output_file="$output_dir/${base_name%.*}.wav"

    echo "[INFO] Processing '$base_name'"

    local total_duration
    total_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_file")

    if ! [[ "$total_duration" =~ ^[0-9.]+$ ]]; then
        echo "[ERROR] Could not get a valid duration for '$base_name'. Skipping."
        return 1
    fi

    local new_duration
    new_duration=$(echo "scale=4; $total_duration - $start_trim - $end_trim" | bc)

    local is_positive
    is_positive=$(echo "$new_duration > 0" | bc)
    if [ "$is_positive" -ne 1 ]; then
        echo "[ERROR] File '$base_name' is too short for the specified trim ($new_duration s). Skipping."
        return 1
    fi

    ffmpeg -y \
        -i "$input_file" \
        -ss "$start_trim" \
        -t "$new_duration" \
        -ar 16000 \
        -ac 1 \
        -af "loudnorm" \
        "$output_file" -loglevel error
}
export -f process_one_file

# --- MAIN EXECUTION ---
echo "[INFO] Starting parallel fixed-time trimming using $N CPUs..."
echo "[INFO] Trimming first ${START_TRIM}s and last ${END_TRIM}s from each file."

find "$INPUT_DIR" -type f \( -iname "*.wav" -o -iname "*.mp3" -o -iname "*.m4a" \) -print0 | \
    xargs -0 -P "$N" -I {} \
    bash -c 'process_one_file "$@"' _ {} "$OUTPUT_DIR" "$START_TRIM" "$END_TRIM"

echo -e "\n[DONE] All audio files have been trimmed and processed successfully."
