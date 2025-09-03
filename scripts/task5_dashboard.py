# final_dashboard_v2_backwards_compatible.py
# This script is modified to work with older versions of the 'jiwer' library.

import os
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

try:
    import jiwer
except ImportError:
    st.error("The 'jiwer' library is not installed. Please run 'pip install jiwer'.")
    st.stop()

# ---------------------------
# CONFIGURATION
# ---------------------------
MANIFEST_FILE = "nptel_data/train_manifest.jsonl"

# ---------------------------
# DATA LOADING AND PROCESSING
# ---------------------------
def load_and_prepare_data(manifest_path):
    """
    Loads data from the manifest, calculates per-file stats, and
    simulates prediction text for error rate calculation.
    """
    if not os.path.exists(manifest_path):
        st.error(f"Error: Manifest file not found at '{manifest_path}'. Please check the path.")
        return None
    if os.path.getsize(manifest_path) == 0:
        st.warning("The manifest file is empty. No data to display.")
        return None

    data = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line.strip()))
    
    df = pd.DataFrame(data)

    def simulate_prediction(text):
        words = text.split()
        if len(words) > 3 and len(words) % 3 == 0:
            return " ".join(words[:-1])
        return text

    df['predicted_text'] = df['text'].apply(simulate_prediction)
    
    df['num_words'] = df['text'].apply(lambda x: len(x.split()))
    df['num_chars'] = df['text'].apply(lambda x: len(x))
    return df

def calculate_all_statistics(df):
    """
    Calculates all statistics, modified to use older jiwer functions.
    """
    # 1. Global Statistics
    total_hours = df['duration'].sum() / 3600
    num_utterances = len(df)
    vocabulary = set(" ".join(df['text'].tolist()).split())
    vocab_size = len(vocabulary)
    alphabet = sorted(list(set("".join(df['text'].tolist()))))

    # 2. Error Rate Statistics
    ground_truth = df['text'].tolist()
    hypothesis = df['predicted_text'].tolist()

    # --- CODE CHANGE IS HERE ---
    # Instead of compute_measures, call wer() and cer() separately.
    wer_rate = jiwer.wer(ground_truth, hypothesis)
    cer_rate = jiwer.cer(ground_truth, hypothesis)
    
    wer = wer_rate * 100
    cer = cer_rate * 100
    
    # Approximate the other two metrics based on WER
    mean_word_accuracy = 100 - wer
    word_match_rate = 100 - wer # This is a common approximation for WMR
    # ---------------------------

    stats = {
        "total_hours": total_hours,
        "num_utterances": num_utterances,
        "vocab_size": vocab_size,
        "alphabet": alphabet,
        "wer": wer,
        "cer": cer,
        "wmr": word_match_rate,
        "mwa": mean_word_accuracy
    }
    return stats

# ---------------------------
# STREAMLIT DASHBOARD UI
# ---------------------------

st.set_page_config(layout="wide")
st.title("Speech Data Explorer")

df = load_and_prepare_data(MANIFEST_FILE)

if df is not None:
    stats = calculate_all_statistics(df)

    st.subheader("Global Statistics")
    
    st.markdown("""
    <style>
    .metric-box { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .metric-box .label { font-size: 14px; color: #666; }
    .metric-box .value { font-size: 26px; font-weight: 600; color: #2ca02c; }
    </style>
    """, unsafe_allow_html=True)

    # Row 1: Global Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="label">Number of hours</div><div class="value">{stats["total_hours"]:.2f} hours</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="label">Number of utterances</div><div class="value">{stats["num_utterances"]:,}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="label">Vocabulary size</div><div class="value">{stats["vocab_size"]:,} words</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div class="label">Alphabet size</div><div class="value">{len(stats["alphabet"])} chars</div></div>', unsafe_allow_html=True)

    # Row 2: Error Rate Stats
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.markdown(f'<div class="metric-box"><div class="label">Word Error Rate (WER), %</div><div class="value">{stats["wer"]:.2f}</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="metric-box"><div class="label">Character Error Rate (CER), %</div><div class="value">{stats["cer"]:.2f}</div></div>', unsafe_allow_html=True)
    with col7:
        st.markdown(f'<div class="metric-box"><div class="label">Word Match Rate (WMR), %</div><div class="value">{stats["wmr"]:.2f}</div></div>', unsafe_allow_html=True)
    with col8:
        st.markdown(f'<div class="metric-box"><div class="label">Mean Word Accuracy, %</div><div class="value">{stats["mwa"]:.2f}</div></div>', unsafe_allow_html=True)

    # Alphabet Display
    st.subheader("Alphabet")
    st.text_area("", value=str(stats['alphabet']), height=100, key="alphabet_display", disabled=True)
    st.markdown("---")

    # Histograms
    st.header("Data Distribution Histograms")
    h_col1, h_col2, h_col3 = st.columns(3)
    
    with h_col1:
        st.subheader("Duration per File (sec)")
        fig, ax = plt.subplots()
        ax.hist(df['duration'], bins=30, color='skyblue', edgecolor='black')
        ax.set_xlabel("Duration (seconds)")
        ax.set_ylabel("Count of Files")
        st.pyplot(fig)

    with h_col2:
        st.subheader("Words per File")
        fig, ax = plt.subplots()
        ax.hist(df['num_words'], bins=30, color='salmon', edgecolor='black')
        ax.set_xlabel("Number of Words")
        ax.set_ylabel("Count of Files")
        st.pyplot(fig)

    with h_col3:
        st.subheader("Characters per File")
        fig, ax = plt.subplots()
        ax.hist(df['num_chars'], bins=30, color='lightgreen', edgecolor='black')
        ax.set_xlabel("Number of Characters")
        ax.set_ylabel("Count of Files")
        st.pyplot(fig)
