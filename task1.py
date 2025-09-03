import os
import re
import requests
import yt_dlp

# ---------------------------
# CONFIG
# ---------------------------
BASE_DIR = "nptel_data"
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "transcripts")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

# ---------------------------
# HELPERS
# ---------------------------
def clean_filename(name):
    """Convert title to Snake_Case and remove invalid characters."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)  # remove invalid chars
    name = re.sub(r"[\s\-]+", "_", name)      # spaces/hyphens → underscore
    return name.strip("_")

def get_drive_id(url):
    """Extract Google Drive file ID from transcript URL."""
    if "drive.google.com" in url:
        parts = url.split("/")
        if "file" in parts and "d" in parts:
            return parts[parts.index("d") + 1]
    return None

# ---------------------------
# DOWNLOAD AUDIO (MODIFIED SECTION)
# ---------------------------
def download_audio(url):
    print(f"[INFO] Downloading audio from: {url}")

    # Step 1: Extract title (This part is unchanged)
    ydl_opts_info = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
        info = ydl.extract_info(url, download=False)
        title = clean_filename(info.get("title", "LectureNA"))

    # Step 2: Download with cleaned title
    outpath = os.path.join(AUDIO_DIR, f"{title}.%(ext)s")
    
    # --- THIS IS THE ONLY CHANGE ---
    # The 'preferredcodec' is changed from 'wav' to 'mp3'.
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outpath,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
        ],
    }
    # -------------------------------

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Update the print statement to reflect the new format.
    print(f"[INFO] Saved audio: {title}.mp3")
    return title

# ---------------------------
# DOWNLOAD TRANSCRIPTS (Unchanged)
# ---------------------------
def download_transcripts(titles_and_links):
    print(f"[INFO] Downloading {len(titles_and_links)} transcripts...")

    for title, url in titles_and_links:
        file_id = get_drive_id(url)
        if not file_id:
            print(f"[WARNING] Skipped invalid link: {url}")
            continue

        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        filename = os.path.join(TRANSCRIPT_DIR, f"{clean_filename(title)}.pdf")

        session = requests.Session()
        try:
            response = session.get(download_url, stream=True, timeout=15)

            if "text/html" in response.headers.get("content-type", "").lower():
                for line in response.text.splitlines():
                    if "confirm=" in line:
                        token = line.split("confirm=")[-1].split("&")[0]
                        confirm_url = f"{download_url}&confirm={token}"
                        response = session.get(confirm_url, stream=True, timeout=15)
                        break

            if response.status_code == 200:
                with open(filename, "wb") as f:
                    for chunk in response.iter_content(1024 * 1024):
                        f.write(chunk)
                print(f"[INFO] Saved transcript: {filename}")
            else:
                print(f"[WARNING] Failed to download (status {response.status_code}): {url}")

        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")

    print("[INFO] Transcript download complete.")

# ---------------------------
# SUMMARY (Slightly modified for consistency)
# ---------------------------
def show_summary():
    # Changed to count .mp3 files instead of .wav
    mp3_count = len([f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")])
    pdf_count = len([f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".pdf")])

    print("\n[SUMMARY]")
    print(f" - Audio (.mp3) files: {mp3_count}")
    print(f" - Transcript (.pdf) files: {pdf_count}")

    if mp3_count != pdf_count:
        print("[WARNING] Mismatch between audio and transcript counts!")
    else:
        print("[INFO] Audio and transcripts look consistent.")

# ---------------------------
# MAIN (Unchanged)
# ---------------------------
if __name__ == "__main__":
    # Step 1: Collect YouTube links
    print("Now enter YouTube video/playlist links (one per line).")
    print("When finished, press ENTER on an empty line.")

    yt_links = []
    while True:
        link = input("YouTube link: ").strip()
        if not link:
            break
        yt_links.append(link)

    audio_titles = []
    if yt_links:
        for link in yt_links:
            title = download_audio(link)
            audio_titles.append(title)
    else:
        print("[INFO] No YouTube links provided.")

    # Step 2: Collect transcript links
    print("\nNow enter Google Drive transcript links (one per line).")
    print("When finished, press ENTER on an empty line.")

    transcript_links = []
    while True:
        link = input("Transcript link: ").strip()
        if not link:
            break
        transcript_links.append(link)

    # Step 3: Match titles with transcripts
    titles_and_links = []
    if len(transcript_links) == len(audio_titles):
        titles_and_links = list(zip(audio_titles, transcript_links))
    else:
        for i, link in enumerate(transcript_links, start=1):
            name = input(f"Enter title for transcript {i} (default = Transcript{i}): ").strip()
            if not name:
                name = f"Transcript{i}"
            titles_and_links.append((name, link))

    if titles_and_links:
        download_transcripts(titles_and_links)
    else:
        print("[INFO] No transcripts provided.")

    # Step 4: Show summary
    show_summary()
    print("\n[DONE] Task 1 completed successfully.")
