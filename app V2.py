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
    stop_words = {
        "the","and","for","that","this","with","you","your","are","was","have","has",
        "media","omitted","message","http","https","will","just","what","there","they",
        "yeah","okay","know","like","want","going"
    }
    # Original .ipynb logic: words longer than 3 chars, lowercased
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

        # --- BAR CHARTS (Properly Labeled) ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Participants")
            top_senders_series = df['Name'].value_counts().head(10)
            if not top_senders_series.empty:
                fig, ax = plt.subplots()
                top_senders_series.plot(kind='bar', ax=ax, color='#25D366')
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

        # --- WORD CLOUD PER TOP 5 SPEAKERS (Inspired by .ipynb) ---
        st.divider()
        st.subheader("☁️ Word Clouds: Top 5 Speakers")
        
        top_5_names = df['Name'].value_counts().head(5).index.tolist()
        
        # Display clouds in a grid (2 rows, 3 columns / 3 rows, 2 columns)
        cols = st.columns(2) 
        
        for i, name in enumerate(top_5_names):
            user_msgs = df[df['Name'] == name]['Message']
            user_text = " ".join([" ".join(clean_text(m)) for m in user_msgs])
            
            with cols[i % 2]:
                if len(user_text.strip()) > 20:
                    wc = WordCloud(width=400, height=300, background_color='white', colormap='Set2').generate(user_text)
                    fig_wc, ax_wc = plt.subplots()
                    ax_wc.imshow(wc, interpolation='bilinear')
                    ax_wc.set_title(f"Words by {name}", fontsize=14, fontweight='bold')
                    ax_wc.axis("off")
                    st.pyplot(fig_wc)
                else:
                    st.write(f"Not enough data for {name}'s Word Cloud.")

        # --- EMOJI & KEYWORDS ---
        st.divider()
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            st.subheader("✨ Top Emojis (All Speakers)")
            all_emojis = []
            for m in df['Message']:
                all_emojis.extend(extract_emojis(str(m)))
            
            emo_counts = Counter(all_emojis).most_common(10)
            if emo_counts:
                emo_df = pd.DataFrame(emo_counts, columns=['Emoji', 'Total Uses'])
                st.write(emo_df.to_html(index=False, classes='emoji-table', escape=False), unsafe_allow_html=True)

        with col_e2:
            st.subheader("👤 Signature Keywords")
            keyword_data = []
            for user in top_5_names:
                u_text = " ".join(df[df['Name']==user]['Message'])
                top_word = Counter(clean_text(u_text)).most_common(1)
                word = top_word[0][0] if top_word else "N/A"
                keyword_data.append({"User": user, "Favorite Word": word})
            
            st.write(pd.DataFrame(keyword_data).to_html(index=False, classes='emoji-table'), unsafe_allow_html=True)

        st.divider()
        search_query = st.text_input("🔍 Search Chat History (Emoji or Word)")
        if search_query:
            results = df[df['Message'].str.contains(search_query, case=False, na=False)]
            st.write(f"Found {len(results)} matches:")
            st.write(results[['Date', 'Name', 'Message']].head(20).to_html(index=False, classes='emoji-table'), unsafe_allow_html=True)
    else:
        st.error("Format Error: Ensure the file is an exported WhatsApp .txt file.")
