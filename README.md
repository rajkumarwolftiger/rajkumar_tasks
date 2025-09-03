# Speech-to-Text Dataset Curation Pipeline for NPTEL Lectures

This project is a comprehensive data engineering pipeline designed to curate a custom Speech-to-Text (STT) dataset from publicly available lectures on NPTEL. The pipeline handles downloading raw data, preprocessing audio and text, creating a training manifest, and visualizing the final dataset statistics.

This document serves as a guide to setting up the environment, executing the pipeline, and understanding the key design choices and observations made during development.

## Project Structure

The project is organized into the following structure to maintain clarity and separation of concerns.

```
task/-
|
|-- scripts/
|     |
|     |-- nptel_data
|     |       |
|     |       |--audio #Having audio file
|     |       |--processed_audio #processed audio from task2 with the (WAV format, with a
|     |       |                   16KHz sampling rate, mono channel format)
|     |       |-- processed_transcripts #process pdf - txt file
|     |       |-- train_manifest.jsonl #created by task4
|     |       |-- transcripts #contain pdf file from task 1
|     |
|     |--task1.py
|     |--task2_process_audio.sh
|     |--task3_process_text.py
|     |--task4_manifest_file.py
|     |--task5_dashboard.py
|
|--LICENSE
|--README.md
|--venv

```

## i. Setup Instructions

Follow these steps to set up the environment required to run all the scripts.

**1. Clone the Repository**
This is a public repository. Clone it using the command.
```bash
git clone rajkumar_tasks
cd rajkumar_tasks
```

**2. System Dependencies**
This project requires `ffmpeg` for audio processing and `yt-dlp` for downloading audio. Please install them using your system's package manager.


**3. Create a Python Virtual Environment**
It is highly recommended to use a virtual environment to manage project dependencies.
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

**4. Install Python Libraries**
Install all required Python libraries from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

## ii. How to Run the Scripts (Pipeline Execution)

The scripts are designed to be run in a sequential pipeline. Please execute them in the following order.

---

### Step 1: Downloading the Data (Task 1)

This Python script downloads the lecture audios and PDF transcripts from a given NPTEL course URL.

<!--ul-->
* Step's: *run the task1.py*

    **Usage:**
    ```bash
    python3 task1.py
    ```
    * *It will ask for a youtube link **copy the link from nptel course page [ Course Details --> week1 --> vedio ] the link should look like this ```https://youtu.be/4TC...``` it's a youtube link** copy the link from the  nptel course page and paste it in the ```bash```, when you paste the links press ```ENTER``` on the empty line and then it will start processing the audio*
    * *When the processing is done for youtube link, then it will ask for a transcript link **copy the link from nptel course page [ Course Details --> Downloads --> Transcripts ] transcript  the link should look like this ```https://drive.google.com/file/d/1wuZcBU6Zk...``` it's a google drive link** copy the google drive and paste in the ```bash```, when you paste the link press ```ENTER``` on the empty line and then it will start processing the pdf files.*

#### This is all for task 1.
---

### Step 2: Preprocessing Audio (Task 2)

This `bash` script processes the raw downloaded audio files. It converts them to `16kHz mono WAV` format, trims silence, and parallelizes the workload across multiple CPU cores.

<!--ul-->
* *Step1: For runing the bash file (.sh) it must be executable.</br>
run this command to make the file executable.*
```bash
chmod +x task2_process_audio.sh
```
* *Step2: run the executable file</br>
    run this command to execute the file and put the input_directory, output_directory and number of **cup's** at the end of the code here is the code.*
```bash
./task2_process_audio.sh ~/rajkumar_tasks/scripts/nptel_data/audio / ~/rajkumar_tasks/scripts/nptel_data/processed_audio / 4
```
*this way we get the ```16kHz mono WAV``` inside the trimmed folder.*

---

### Step 3: Preprocessing Text (Task 3)

This Python script cleans the raw text extracted from the PDFs. It converts text to lowercase, removes punctuation, and expands numbers into their spoken-word form.

<!--ul-->
* *Steps: run the task 3 python file.</br> here is the command to run the task 3.*
```bash
python3 task3_process_text.py
```
#### *this command will run the task 3, it will take .pdf files from the transcript folder and extract the text to the .txt file format to the transcript_process folder*

---

### Step 4: Creating the Training Manifest (Task 4)

This script aligns the processed audio and text files and generates the final `train_manifest.jsonl` file, which is required for training STT models.

<!--ul-->
* *step's: run the task4 python file.</br> here is the command to tun the task 4.*
```bash
python3 task4_manifest_file.py
```
### *this command will run the task 4, it will take audio from ```process_audio/trimmed``` directory (16kHz mono WAV) and text from ```process_transcript``` directory (.txt file) and give the output in the nptel/train_manifest.jsonl*

### *here is the sample output:*
```bash
{"audio_filepath": "processed_audio/Deep_Learning(CS7015)_Lec_1.1_Biological_Neuron_16k_mono.wav", 
"duration": 417.681, 
"text": "hello everyone welcome to lecture of cs  which is the course on deep learning in today’s lecture is going to be a bit non technical we are not going to cover any technical concepts or we only going to talk about a brief or partial history of deep learning so we hear the terms artificial neural networks artificial neurons quite often these days and i just wanted you take you through the journey of where does all these originate from and this history contains several spans across several fields
```

---

### Step 5: Creating a Dashboard (Bonus Task 5)

This script launches an interactive web dashboard using Streamlit to visualize key statistics of the curated dataset.

**Usage:**
```bash
streamlit run task5_dashboard.py
```
*this command wil give you the link of the dashboard.</br> It should look like this.*
```bash
You can now view your Streamlit app in your browser.

 Local URL: http://localhost:8501
 Network URL: http://172.25.241.142:8501

```
### This is all for the tasks steps. 

---
---

## iii. Your Observations on the Process

### Task 1: Data Downloading
When testing the download script on a different NPTEL course, I observed that its robustness depends heavily on the consistency of the NPTEL website's HTML structure. The current script is tailored to the layout of the specified Deep Learning course. A more robust, production-grade scraper would require more sophisticated logic to handle variations in page layouts across different courses, potentially using more flexible selectors or fallback mechanisms.

### Task 2: Audio Preprocessing
- **Challenge - End-of-Lecture Content:** As hinted, listening to the audio revealed that the last 10-20 seconds often contain outro music, credits, or acknowledgments not present in the transcript. This creates a severe audio-text mismatch.
- **Solution:** I implemented a solution within the `task2_process_audio.sh` script to automatically trim the last 10 seconds from every audio file before any other processing. This is a simple but highly effective heuristic for cleaning up lecture-style content.
- **Parallelization:** Implementing parallel processing in the bash script significantly sped up the audio conversion. The script spawns background processes up to the user-defined CPU limit (`N`), making it scalable for large datasets with thousands of files.

### Task 3: Text Preprocessing
- **Challenge - Audio-Text Misalignment:** This was the most critical data quality issue. The PDF transcripts often contained introductory text (e.g., course title, professor's name) that was displayed on a title slide but was not spoken in the audio. The processed audio, after silence trimming, would start with the first spoken words, creating a mismatch.
- **Solution:** The ideal solution is a manual alignment step where a human listens to the start of each audio clip and cleans the corresponding transcript. For this project's scope, I noted this as a critical next step for quality assurance. An automated approach could involve using a pre-trained ASR model to get a rough transcript of the first few seconds and then perform a string alignment to find the correct starting point in the text, but this is complex.
- **`num2words` Library:** This library was effective for converting digits to words, which is crucial as STT models learn to map sounds to words, not digits.

### Task 5: Dashboard and Metrics
- **Tool Choice:** I chose **Streamlit** for the dashboard because it allows for rapid development of interactive data applications directly in Python, making it a perfect fit for this pipeline.
- **Simulated Metrics:** The example dashboard showed metrics like Word Error Rate (WER). Calculating WER requires a model's predictions to compare against the ground truth. Since predictions were not available, I simulated a "predicted text" column in the dashboard script by introducing artificial errors. This demonstrates how the evaluation UI would work in a full MLOps pipeline and shows the calculated error rates are for demonstration purposes only.

### Final Included Artifacts
- The generated `train_manifest.jsonl` is included in the nptel_data directory.
- The processed audios for the first 5 lines of the manifest are in the `nptel_data/train_manifest.jsonl` directory.

---
---
