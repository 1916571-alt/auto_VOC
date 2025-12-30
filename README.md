# VOC Intelligence Playground

## Project Overview
This project transforms unstructured customer reviews (VOC) into actionable insights using RAG (Retrieval-Augmented Generation) and statistical analysis. It aims to automate the reporting process and provide tangible data for product improvement.

## Features
- **Data Ingestion**: Specific format support for VOC data.
- **RAG Analysis**: Uses Gemini to classify reviews and extract key issues.
- **Automated Reporting**: Generates markdown reports with strict formatting.
- **Notification**: Integration with Slack/Discord (configured in `teams.yaml`).

## Tech Stack
- Python 3.10+
- Streamlit
- LangChain / LangChain Google GenAI
- ChromaDB
- Pandas, Scipy

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up environment variables:
   - `GOOGLE_API_KEY`
3. Run the valid mock data generator:
   ```bash
   python generate_data.py
   ```
4. Run the application (coming soon):
   ```bash
   streamlit run app.py
   ```

## Configuration
- Modify `config/teams.yaml` to map keywords and teams.

## Structure
- `analyzer.py`: Core RAG analysis logic.
- `data/`: Stores raw data and vector embeddings.
- `utils/`: Utility functions for notifications.
