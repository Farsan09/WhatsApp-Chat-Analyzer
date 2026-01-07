# WhatsApp Chat Analyzer (V2 Optimized)

A high-performance Python tool designed to transform raw WhatsApp export files (`.txt`) into structured data and visual insights. This updated version replaces the traditional string-splitting method with **Regular Expression (Regex) parsing**, significantly improving speed and accuracy for complex chat formats.

---

## ✨ New in V2

* **Regex Engine**: Uses advanced pattern matching to handle unique WhatsApp timestamps, including those with narrow-no-break spaces (e.g., `10:24 am`).
* **NLP & Word Clouds**: Automatically generates word clouds for the top 5 most active participants while filtering out common "stop words" and media markers.
* **Non-Blocking GUI**: Integrated `tkinter` file dialog for easy file selection without the "upload freeze" experienced in earlier versions.
* **Comprehensive Visualizations**: Provides a 4-quadrant dashboard covering sender activity, daily message frequency, and top word usage.

---

## 📊 Visual Insights

The analyzer generates the following reports automatically:

* **Top 5 Active People**: Bar chart identifying the most frequent senders.
* **Messages Per Day**: Line graph showing conversation trends over the entire history of the chat.
* **Top Words Used**: A bar chart of the most common meaningful words after removing noise.
* **Member Word Clouds**: A visual representation of the unique vocabulary used by each top participant.

---

## 🛠️ Setup & Requirements

Ensure you have the following Python libraries installed:

```bash
pip install pandas matplotlib wordcloud

```

* **Pandas**: For data structuring and CSV export.
* **Matplotlib**: For rendering the statistical charts.
* **WordCloud**: For generating the visual NLP summaries.
* **Tkinter**: For the file selection interface (usually built-in).

---

## 📖 How to Run

1. **Export Chat**: Open WhatsApp -> Choose a Chat -> Export Chat -> **Without Media**.
2. **Launch**: Run the `Automatic Analyzer V2.ipynb` notebook.
3. **Select File**: When the file explorer appears, select your exported `.txt` file.
4. **Analyze**: The script will automatically parse the data, display charts, and save a file named `cleaned_whatsapp_chat.csv` to your directory.

---

## ⚠️ Compatibility Note

This version is specifically tuned for the modern WhatsApp export format: `DD/MM/YYYY, HH:MM am/pm - Name: Message`. If your format differs (e.g., 24-hour time without am/pm), the Regex pattern in the `perform_analysis` function can be easily adjusted.

