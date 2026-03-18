import streamlit as st
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

# Custom CSS to make the HTML tables look like Streamlit tables
st.markdown("""
    <style>
    .reportview-container .main .block-container { max-width: 90%; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; font-family: sans-serif; }
    th { background-color: #f0f2f6; color: #31333f; text-align: left; padding: 12px; border: 1px solid #dee2e6; }
    td { padding: 10px; border: 1px solid #dee2e6; color: #31333f; }
    tr:nth-child(even) { background-color: #f8f9fb; }
    </style>
    """, unsafe_allow_html=True)

STOP_WORDS = {
    "the","and","for","that","this","with","you","your","are","was","have",
    "has","but","not","from","they","their","will",
    "media","omitted","dey","una","don","wan","sef","make","message","sha","say","see"
}

# REGEX PATTERNS: Fixed to avoid "unbalanced parenthesis" errors
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
    
    # Get the raw bytes
    raw_bytes = uploaded_file.getvalue()
    
    # Try multiple encodings
    content = None
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "utf-16"]:
        try:
            content = raw_bytes.decode(encoding)
            break # If it works, stop trying
        except UnicodeDecodeError:
            continue
            
    if content is None:
        st.error("Could not decode the file. Please try exporting the chat again.")
        return pd.DataFrame()

    stringio = io.StringIO(content)
    
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
    df['Full_Timestamp'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'].str.replace('\u202f', ' ', regex=False),
        dayfirst=True, 
        errors='coerce'
    )
    df = df.dropna(subset=['Full_Timestamp'])
    df['Hour'] = df['Full_Timestamp'].dt.hour
    df['Date_Only'] = df['Full_Timestamp'].dt.date
    df['Length'] = df['Message'].str.len()
    
    return df

# --- 3. STREAMLIT UI ---
st.title("📊 WhatsApp Chat Analyzer")

uploaded_file = st.file_uploader("Step 1: Upload your WhatsApp .txt export", type="txt")

if uploaded_file:
    df = parse_whatsapp(uploaded_file)
    
    if not df.empty:
        # --- SIDEBAR FILTERS ---
        st.sidebar.header("🗓️ Filter Options")
        min_date = df['Date_Only'].min()
        max_date = df['Date_Only'].max()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df['Date_Only'] >= start_date) & (df['Date_Only'] <= end_date)
            df = df.loc[mask]

        st.success(f"Successfully loaded {len(df)} messages!")
        
        # --- DASHBOARD VISUALS ---
        top_senders = df['Name'].value_counts().head(5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 5 Active Participants")
            fig, ax = plt.subplots()
            top_senders.plot(kind='bar', ax=ax, color='#4CAF50')
            ax.set_ylabel("Messages")
            st.pyplot(fig)
            
        with col2:
            st.subheader("Hourly Activity (24h)")
            hourly = df['Hour'].value_counts().sort_index().reindex(range(24), fill_value=0)
            fig, ax = plt.subplots()
            ax.bar(hourly.index, hourly.values, color='#2196F3')
            ax.set_xticks(range(24))
            st.pyplot(fig)

        # --- WORD CLOUDS ---
        st.divider()
        st.subheader("☁️ Word Clouds (Top 3 Senders)")
        valid_names = top_senders.index[:3] 
        cols = st.columns(len(valid_names))
        
        for i, name in enumerate(valid_names):
            combined_msgs = " ".join(df[df['Name']==name]['Message'])
            tokens = clean_text(combined_msgs)
            if len(tokens) > 5:
                wc = WordCloud(background_color="white", width=400, height=400).generate(" ".join(tokens))
                with cols[i]:
                    fig, ax = plt.subplots()
                    ax.imshow(wc, interpolation='bilinear')
                    ax.set_title(name)
                    ax.axis("off")
                    st.pyplot(fig)

        # --- HTML TABLE BYPASS (Fixes PyArrow DLL Error) ---
        st.divider()
        st.subheader("👤 Top Keywords per Sender")
        summary_list = []
        for name in top_senders.index:
            tokens = []
            for msg in df[df['Name'] == name]['Message']:
                tokens.extend(clean_text(msg))
            top_5 = [w for w, _ in Counter(tokens).most_common(5)]
            summary_list.append({"Sender": name, "Most Used Words": ", ".join(top_5)})
        
        summary_df = pd.DataFrame(summary_list)
        # Rendering as HTML table to avoid PyArrow
        st.write(summary_df.to_html(index=False, escape=False), unsafe_allow_html=True)

        # --- SEARCH BAR ---
        st.divider()
        st.subheader("🔍 Search Chat History")
        query = st.text_input("Type a keyword to search (e.g. 'work', 'lunch', 'lol')")
        if query:
            search_results = df[df['Message'].str.contains(query, case=False, na=False)]
            st.write(f"Found {len(search_results)} messages.")
            # Rendering search results as HTML to avoid PyArrow
            st.write(
                search_results[['Date', 'Name', 'Message']].head(20).to_html(index=False), 
                unsafe_allow_html=True
            )

    else:
        st.error("Format Error: Could not read chat. Ensure you used the 'Export Chat' (Without Media) option.")
