# task3_process_text.py (Final Corrected Version with Forced Alignment)

import os
import re
import string
import argparse
import whisper_timestamped as whisper
import pdfplumber
from num2words import num2words
from tqdm import tqdm

def align_and_extract_text(audio_path: str, raw_pdf_text: str, model) -> str:
    """
    Performs forced alignment to find the exact text in the PDF that
    matches the audio content.
    """
    try:
        # --- THIS IS THE CRITICAL FIX ---
        # The library expects the transcript text to be passed via the 'initial_prompt' argument, not 'text'.
        result = whisper.transcribe(
            model,
            audio_path,
            initial_prompt=raw_pdf_text, # CORRECTED ARGUMENT
            language="en"
        )
        # --------------------------------

        # Reconstruct the transcript ONLY from the aligned segments.
        # This automatically discards any non-spoken intro/outro text from the PDF.
        aligned_text = " ".join(segment['text'].strip() for segment in result['segments'])
        
        return aligned_text

    except Exception as e:
        print(f"\n[WARNING] Forced alignment failed for {os.path.basename(audio_path)}: {e}. Falling back to full text.")
        return raw_pdf_text

def clean_aligned_text(text: str) -> str:
    """
    Applies the final cleaning steps (lowercase, punctuation, numbers) to the
    perfectly aligned text.
    """

    text = re.sub(r'\s+', ' ', text).strip()
    
    def _replace_digits(match):
        try: return num2words(match.group(0))
        except: return match.group(0)
    text = re.sub(r'\d+', _replace_digits, text)

    text = text.lower()
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def process_all_files(pdf_dir: str, audio_dir: str, txt_dir: str):
    """
    Main function to process all PDFs, aligning them with their corresponding audio files.
    """
    os.makedirs(txt_dir, exist_ok=True)
    
    print("[INFO] Loading Whisper ASR model for alignment (this may take a moment)...")
    try:
        whisper_model = whisper.load_model("base.en")
    except Exception as e:
        print(f"[FATAL] Could not load Whisper model. Error: {e}")
        return

    pdf_map = {os.path.splitext(f)[0]: os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')}
    audio_map = {os.path.splitext(f)[0]: os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.lower().endswith('.wav')}

    if not pdf_map:
        print(f"[WARNING] No PDF files found in '{pdf_dir}'.")
        return

    print(f"[INFO] Found {len(pdf_map)} PDFs to process. Starting forced alignment...")
    
    for core_name, pdf_path in tqdm(pdf_map.items(), desc="Aligning Transcripts"):
        if core_name not in audio_map:
            print(f"\n[WARNING] No matching PROCESSED audio found for '{core_name}.pdf'. Skipping.")
            continue
        
        audio_path = audio_map[core_name]

        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_raw_text = "".join(page.extract_text() or "" for page in pdf.pages)
            
            if not full_raw_text.strip():
                continue

            aligned_text = align_and_extract_text(audio_path, full_raw_text, whisper_model)
            final_text = clean_aligned_text(aligned_text)

            output_path = os.path.join(txt_dir, core_name + ".txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_text)

        except Exception as e:
            print(f"\n[ERROR] A critical error occurred while processing '{os.path.basename(pdf_path)}': {e}")
    
    print("\n[DONE] Task 3 completed with forced alignment.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Align and clean PDF transcripts using processed audio files.")
    parser.add_argument("--pdf_dir", default="nptel_data/transcripts", help="Path to the directory with raw PDF transcripts.")
    parser.add_argument("--audio_dir", default="nptel_data/processed_audio", help="Path to the directory with PROCESSED audio files from Task 2.")
    parser.add_argument("--txt_dir", default="nptel_data/processed_transcripts", help="Path to save cleaned and aligned .txt files.")
    
    args = parser.parse_args()
    
    process_all_files(args.pdf_dir, args.audio_dir, args.txt_dir)
