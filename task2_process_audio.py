# task2_process_audio.py
# This version has the trim times (12s start, 31s end) hardcoded.

import os
import subprocess
import argparse
from multiprocessing import Pool
from tqdm import tqdm

def process_file(args_tuple):
    """
    Worker function that processes a single audio file with fixed trim times.
    """
    input_file, output_dir = args_tuple
    base_name = os.path.basename(input_file)
    output_file = os.path.join(output_dir, os.path.splitext(base_name)[0] + ".wav")
    
    # --- HARDCODED TRIM TIMES ---
    # CHANGED: The trim durations are now fixed inside the script.
    start_trim = 12.0
    end_trim = 30.0
    # ---------------------------

    try:
        # 1. Get total duration using ffprobe
        ffprobe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", input_file
        ]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())

        # 2. Calculate new duration
        new_duration = total_duration - start_trim - end_trim

        # 3. Validate duration
        if new_duration <= 0:
            return f"[WARNING] Skipping '{base_name}': File too short for trim."

        # 4. Run ffmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", input_file, "-ss", str(start_trim),
            "-t", str(new_duration), "-ar", "16000", "-ac", "1",
            "-af", "loudnorm", output_file
        ]
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return None # Return None on success

    except Exception as e:
        return f"[ERROR] Failed processing '{base_name}': {e}"


if __name__ == "__main__":
    # CHANGED: The command now only takes 3 arguments
    parser = argparse.ArgumentParser(description="A robust script to preprocess audio files in parallel.")
    parser.add_argument("input_dir", help="Path to the directory containing all audio files.")
    parser.add_argument("output_dir", help="Path to an output directory to store the processed files.")
    parser.add_argument("num_cpus", type=int, help="Number of CPU cores to use for parallel processing.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    files_to_process = []
    valid_extensions = ('.wav', '.mp3', '.m4a', '.opus')
    for filename in os.listdir(args.input_dir):
        if filename.lower().endswith(valid_extensions):
            files_to_process.append(os.path.join(args.input_dir, filename))

    if not files_to_process:
        print(f"[ERROR] No audio files found in '{args.input_dir}'.")
        exit(1)
        
    tasks = [(f, args.output_dir) for f in files_to_process]

    print(f"[INFO] Starting parallel fixed-time trimming using {args.num_cpus} CPUs...")
    print(f"[INFO] Trimming first 12s and last 31s from each file.")

    with Pool(processes=args.num_cpus) as pool:
        results = list(tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks)))

    # Print any errors that occurred
    for res in results:
        if res:
            print(res)

    print("\n[DONE] All audio files have been trimmed and processed successfully.")
