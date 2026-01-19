# Anti-Piracy RSS Searcher

This project is a tool to monitor RSS feeds and perform Google searches to detect content related to digital piracy. It filters results based on specific keywords and generates a CSV report.

## Requirements

- Python 3.8+

## Installation

1. Clone the repository or download the folder.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_api_key_here
   GOOGLE_CSE_ID=your_cse_id_here
   ```
   **Why do I need these keys?**
   This tool uses the **Google Custom Search JSON API** to perform automated searches for piracy-related keywords (e.g., "IPTV", "cardsharing") on the web. This allows it to find relevant articles that might not appear in the monitored RSS feeds.

2. Ensure you have your Google API credentials ready.

## Usage

Run the main script:
```bash
python BuscadorRSS_filtrado.py
```

The script will generate a csv file with the relevant results found.
