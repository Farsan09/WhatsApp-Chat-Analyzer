# WhatsApp Chat Analyzer (String-Split Method)

A lightweight, automated Python tool designed to parse, clean, and visualize exported WhatsApp chat data. This project provides a quick way to transform raw `.txt` chat exports into structured data frames and insightful visualizations.

---

## 🚀 Features

* **GUI File Selection**: Uses `tkinter` to provide a user-friendly file explorer for selecting your chat export.
* **Automatic Parsing**: Implements a string-split methodology to extract **Date**, **Time**, **Sender Name**, and **Message Content**.
* **Data Analysis**:
* Calculates message lengths to identify the most talkative participants.
* Identifies the top 5 most active senders.
* Finds and displays the longest individual messages.


* **Visualizations**: Generates bar charts for sender activity and time-series line plots for message frequency over time using `matplotlib`.
* **Data Export**: Automatically saves the cleaned and processed data as `cleaned_whatsapp_chat.csv` for further Natural Language Processing (NLP) or deep analysis.

---

## 🛠️ Prerequisites

To run this notebook, you will need the following Python libraries:

* **pandas**: For data manipulation and CSV export.
* **matplotlib**: For generating charts and plots.
* **tkinter**: For the file selection interface (usually included with standard Python installations).

```bash
pip install pandas matplotlib

```

---

## 📖 How to Use

1. **Export your WhatsApp Chat**:
* Open a chat in WhatsApp.
* Tap the three dots (Android) or the contact name (iOS).
* Select **More** > **Export Chat**.
* Choose **Without Media** to generate a `.txt` file.


2. **Run the Notebook**: Open `Automatic Analyser.ipynb` in your preferred Jupyter environment (VS Code, JupyterLab, etc.).
3. **Execute the Cells**: Run the cells in order. A file dialog will appear; select your exported `.txt` file.
4. **View Results**: The script will output statistical summaries and display visualizations directly in the notebook.

---

## 📊 Sample Visualizations

The tool generates two primary insights:

1. **Top 5 Active People**: A bar chart showing who sent the most messages.
2. **Messages Per Day**: A line graph tracking conversation volume over the history of the chat.

---

## ⚠️ Important Notes

* **Format Compatibility**: This analyzer uses a specific string-splitting logic based on standard WhatsApp export formats. If your export format differs significantly (due to OS variations or regional settings), the parsing logic in the `run_whatsapp_analysis` function may need minor adjustments.
* **Privacy**: This script processes data locally on your machine. Ensure you handle exported chat files securely as they contain private conversations.
