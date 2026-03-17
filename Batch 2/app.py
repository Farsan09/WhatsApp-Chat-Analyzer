import streamlit as st
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import io

# --- 1. CONFIGURATION & PATTERNS ---
st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

STOP_WORDS = {
    "the","and","for","that","this","with","you","your","are","was","have",
    "has","but","not","from","they","their","will",
    "media","omitted","dey","una","don","wan","sef","make","message","sha","say","see"
}

# FIXED REGEX: Escaped brackets to avoid "unbalanced parenthesis"
IPHONE_PATTERN = re.compile(
    r'^\[(\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}),\s*'
    r'(\d{1,2}:\d{2}(?::\d{2})?\s*[APMapm]{2})\]\s*'
    r'(.+?):\s*(.*)$'
)

ANDROID_PATTERN = re.compile(
    r'^(\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}),\s*'
    r'(\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)\s*-\s*'
    r'(.+?):\s*(.*)$'
)

# --- 2. HELPER FUNCTIONS ---
def clean_text(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', str(text).lower())
    return [w for w in words if w not in STOP_WORDS]

def normalize_line(line: str) -> str:
    return (
        line.replace("\ufeff", "").replace("\u200e", "")
        .replace("\u202a", "").replace("\u202c", "")
        .replace("\u202f", " ").lstrip()
    )

def parse_whatsapp(uploaded_file):
    data = []
    current_message = None
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8-sig"))
    
    for raw_line in stringio:
        line = normalize_line(raw_line)
        match = IPHONE_PATTERN.match(line) or ANDROID_PATTERN.match(line)

        if match:
            if current_message:
                data.append(current_message)
            current_message = list(match.groups())
        else:
            if current_message:
                current_message[3] += " " + line.strip()

    if current_message:
        data.append(current_message)
    
    df = pd.DataFrame(data, columns=['Date', 'Time', 'Name', 'Message'])

    # --- ROBUST DATE FIX ---
    # Combines Date and Time, then uses dayfirst=True to handle both DD/MM and MM/DD safely
    df['Full_Timestamp'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'].str.replace('\u202f', ' ', regex=False),
        dayfirst=True, 
        errors='coerce'
    )
    df = df.dropna(subset=['Full_Timestamp'])
    df['Hour'] = df['Full_Timestamp'].dt.hour
    df['Length'] = df['Message'].str.len()
    
    return df

# --- 3. STREAMLIT UI ---
st.title("📊 WhatsApp Chat Analyzer")

uploaded_file = st.file_uploader("Upload WhatsApp .txt export", type="txt")

if uploaded_file:
    df = parse_whatsapp(uploaded_file)
    
    if not df.empty:
        st.success(f"Parsed {len(df)} messages successfully!")
        
        # Dashboard Logic
        top_senders = df['Name'].value_counts().head(5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 5 Active Participants")
            fig, ax = plt.subplots()
            top_senders.plot(kind='bar', ax=ax)
            st.pyplot(fig)
            
        with col2:
            st.subheader("Hourly Activity")
            hourly = df['Hour'].value_counts().sort_index()
            fig, ax = plt.subplots()
            ax.bar(hourly.index, hourly.values)
            st.pyplot(fig)

        # Word Clouds
        st.divider()
        st.subheader("Participant Word Clouds")
        valid_names = top_senders.index[:3] # Show top 3 to save space
        cols = st.columns(len(valid_names))
        
        for i, name in enumerate(valid_names):
            text = " ".join([" ".join(clean_text(m)) for m in df[df['Name']==name]['Message']])
            if len(text) > 10:
                wc = WordCloud(background_color="white").generate(text)
                with cols[i]:
                    fig, ax = plt.subplots()
                    ax.imshow(wc)
                    ax.set_title(name)
                    ax.axis("off")
                    st.pyplot(fig)
    else:
        st.error("Format not recognized. Check your export file.")
