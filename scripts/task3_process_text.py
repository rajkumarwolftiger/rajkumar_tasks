import os
import re
import glob
import string
import pdfplumber
from num2words import num2words

# ---------------------------
# CONFIG
# ---------------------------
INPUT_DIR = "nptel_data/transcripts"          # PDF transcripts
OUTPUT_DIR = "nptel_data/processed_transcripts"  # Cleaned .txt files

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------
# CLEANING FUNCTION
# ---------------------------
def preprocess_text(raw_text: str) -> str:
    """Clean transcript text for Task 3."""
    # Remove page numbers like "Page 1 of 20"
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", raw_text, flags=re.IGNORECASE)

    # Remove standalone numbers (headers/footers)
    text = re.sub(r"\n?\s*\d+\s*\n?", " ", text)

    # Remove non-spoken segments like slides or references
    text = re.sub(r"\(Refer Slide.*?\)", " ", text)
    text = re.sub(r"\(\s*\)", " ", text)
    text = re.sub(r"\[.*?\]", " ", text)

    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text)

    # Split into sentences to filter very short lines
    lines = text.split('. ')
    cleaned_lines = []
    skip_keywords = ["figure", "table", "reference", "copyright", "©", "www", "http"]

    for line in lines:
        line_stripped = line.strip()
        if len(line_stripped.split()) < 3:
            continue  # Skip very short lines
        if any(keyword in line_stripped.lower() for keyword in skip_keywords):
            continue
        cleaned_lines.append(line_stripped)

    text = '. '.join(cleaned_lines)

    # Convert digits to words
    def replace_digits(match):
        return num2words(match.group())
    text = re.sub(r"\d+", replace_digits, text)

    # Convert to lowercase
    text = text.lower()

    # Remove all punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    return text.strip()

# ---------------------------
# PROCESS ALL PDFs
# ---------------------------
def process_pdfs():
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))

    if not pdf_files:
        print(f"[WARNING] No PDFs found in {INPUT_DIR}")
        return

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"[INFO] Processing {idx}/{len(pdf_files)}: {pdf_file}")

        try:
            with pdfplumber.open(pdf_file) as pdf:
                page_texts = []
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        page_texts.append(page_text)

                raw_text = "\n".join(page_texts)

            if not raw_text.strip():
                print(f"[WARNING] Skipping {pdf_file} (no usable text).")
                continue

            cleaned = preprocess_text(raw_text)

            # Save cleaned text
            base_name = os.path.basename(pdf_file).replace(".pdf", ".txt")
            out_file = os.path.join(OUTPUT_DIR, base_name)

            with open(out_file, "w", encoding="utf-8") as f:
                f.write(cleaned)

            print(f"[INFO] Saved cleaned transcript → {out_file}")

        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_file}: {e}")

    txt_files = glob.glob(os.path.join(OUTPUT_DIR, "*.txt"))
    print("\n[SUMMARY]")
    print(f" - Processed PDFs: {len(pdf_files)}")
    print(f" - Generated TXT files: {len(txt_files)}")
    print("\n[DONE] Task 3 completed successfully.")

# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    process_pdfs()
