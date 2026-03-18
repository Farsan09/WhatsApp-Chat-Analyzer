import streamlit as st
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import io

# --- 1. CONFIGURATION & GLOBAL STYLING ---
st.set_page_config(page_title="WhatsApp Chat Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .emoji-table { 
        width: 100%; 
        border-collapse: collapse; 
        font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
    }
    .emoji-table th { background-color: #075E54; color: white; text-align: left; padding: 12px; }
    .emoji-table td { padding: 10px; border: 1px solid #dee2e6; font-size: 18px; }
    tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC FUNCTIONS ---
def extract_emojis(text):
    return re.findall(r'[^\w\s,.;:!?-]', text)

def clean_text(text):
    # Added common chat filler words to stop_words
    stop_words = {
        "the","and","for","that","this","with","you","your","are","was","have","has",
        "media","omitted","message","http","https","will","just","what","there","they"
    }
    words = re.findall(r'\b[a-zA-Z]{4,}\b', str(text).lower())
    return [w for w in words if w not in stop_words]

def parse_whatsapp(uploaded_file):
    raw_bytes = uploaded_file.getvalue()
    content = None
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            content = raw_bytes.decode(enc)
            break
        except: continue
    
    if not content: return pd.DataFrame()

    iphone_reg = re.compile(r'^\[(\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APMapm]{2})?)\]\s*(.+?):\s*(.*)$')
    android_reg = re.compile(r'^(\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}),\s*(\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)\s*-\s*(.+?):\s*(.*)$')

    data = []
    current_msg = None

    for line in content.split('\n'):
        line = line.strip()
        if not line: continue
        match = iphone_reg.match(line) or android_reg.match(line)
        if match:
            if current_msg: data.append(current_msg)
            current_msg = list(match.groups())
        elif current_msg:
            current_msg[3] += " " + line

    if current_msg: data.append(current_msg)
    if not data: return pd.DataFrame()

    df = pd.DataFrame(data, columns=['Date', 'Time', 'Name', 'Message'])
    df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Timestamp'])
    df['Date_Only'] = df['Timestamp'].dt.date
    df['Hour'] = df['Timestamp'].dt.hour
    return df

# --- 3. STREAMLIT UI ---
st.title("📊 WhatsApp Analytics Dashboard")

file = st.file_uploader("Upload WhatsApp Export (.txt)", type="txt")

if file:
    df = parse_whatsapp(file)
    
    if not df.empty:
        all_dates = sorted(df['Date_Only'].unique())
        if len(all_dates) > 1:
            dr = st.sidebar.date_input("Filter by Date Range", [all_dates[0], all_dates[-1]])
            if isinstance(dr, (list, tuple)) and len(dr) == 2:
                df = df[(df['Date_Only'] >= dr[0]) & (df['Date_Only'] <= dr[1])]

        st.success(f"Analyzed {len(df)} messages successfully.")

        # --- BAR CHARTS ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Participants")
            top_senders = df['Name'].value_counts().head(10)
            if not top_senders.empty:
                fig, ax = plt.subplots()
                top_senders.plot(kind='bar', ax=ax, color='#25D366')
                ax.set_xlabel("Participant Name")
                ax.set_ylabel("Number of Messages")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)
        
        with col2:
            st.subheader("Activity by Hour")
            hr_data = df['Hour'].value_counts().sort_index().reindex(range(24), fill_value=0)
            fig, ax = plt.subplots()
            ax.bar(hr_data.index, hr_data.values, color='#34B7F1')
            ax.set_xlabel("Hour of Day (24h Format)")
            ax.set_ylabel("Message Count")
            ax.set_xticks(range(0, 24))
            st.pyplot(fig)

        # --- WORD CLOUD SECTION ---
        st.divider()
        st.subheader("☁️ Most Frequent Words (Word Cloud)")
        all_words = " ".join([" ".join(clean_text(m)) for m in df['Message']])
        
        if len(all_words.strip()) > 10:
            wordcloud = WordCloud(width=800, height=400, background_color='white', 
                                  colormap='viridis', min_font_size=10).generate(all_words)
            fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
            ax_wc.imshow(wordcloud, interpolation='bilinear')
            ax_wc.axis("off")
            st.pyplot(fig_wc)
        else:
            st.write("Not enough text data to generate a word cloud.")

        # --- EMOJI & KEYWORDS ---
        st.divider()
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            st.subheader("✨ Top Emojis")
            all_emojis = []
            for m in df['Message']:
                all_emojis.extend(extract_emojis(str(m)))
            
            emo_counts = Counter(all_emojis).most_common(10)
            if emo_counts:
                emo_df = pd.DataFrame(emo_counts, columns=['Emoji', 'Total Uses'])
                st.write(emo_df.to_html(index=False, classes='emoji-table', escape=False), unsafe_allow_html=True)
            else:
                st.write("No emojis detected.")

        with col_e2:
            st.subheader("👤 Signature Keywords")
            keyword_data = []
            for user in df['Name'].value_counts().head(5).index:
