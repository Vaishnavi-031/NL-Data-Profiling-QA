# NL Data Profiling Q&A

An AI-powered system for querying ydata-profiling reports using natural language.

For team details and responsibilities, refer to `TEAM_INFO.md`.

This prototype enables users to upload CSV datasets, automatically generate detailed profiling reports, and query these reports using natural language. It addresses the limitation of static ydata-profiling reports by providing an interactive chat interface powered by Gemini.

## Problem Statement
`ydata-profiling` generates comprehensive static data quality reports (as HTML/JSON), but navigating these reports to answer specific questions can be tedious. Users should be able to upload a CSV file and query the report directly in natural language (e.g., "Which column has the most null values?", "Are there duplicate rows?", "Which columns are highly correlated?").

---

## Architecture Overview

The prototype follows a clean, modular structure:

```
User ➔ Streamlit UI (app.py) ➔ Profiler (src/profiler.py) ➔ outputs/profile.json
                        │
                        ▼
                Agent Core (src/agent.py) ➔ Retrieval (src/retrieval.py)
                        │
                        ▼
                Gemini LLM Helper (src/llm_helper.py) ➔ Structured JSON Response
```

1. **Streamlit UI (`app.py`)**: Provides a user-friendly frontend for CSV upload, dashboard metrics, report downloading, and chat.
2. **Profiler (`src/profiler.py`)**: Uses `ydata-profiling` to compile an HTML report and a structured JSON dataset summary.
3. **Retrieval (`src/retrieval.py`)**: Performs keyword-based scans on the generated `profile.json` to extract precise table statistics, warnings, correlations, and column info as a clean context text.
4. **LLM Helper (`src/llm_helper.py`)**: Wraps the Google Generative AI SDK, passing context and user queries to `gemini-1.5-flash` to generate a structured JSON response.
5. **Agent Core (`src/agent.py`)**: Coordinates the query-retrieval-LLM loop and validates the output schema and citations against the report parameters.

---

## Technologies Used
- **Python 3.11**
- **Streamlit** (User Interface)
- **Pandas** (Data handling)
- **ydata-profiling** (Data profiling report generator)
- **Google Generative AI SDK** (`google-generativeai` package interfacing Gemini)
- **python-dotenv** (Environment configuration)
- **Pytest** (Automated unit testing)

---

## Setup Instructions

1. Clone or copy the project files to your workspace directory.
2. Ensure you have Python 3.11 installed.
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your Gemini API Key:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```

   - Open `.env` and add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_api_key_here
     ```

---

## Run Instructions

1. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
2. Open the URL provided in your terminal (typically `http://localhost:8501`).

---

## Sample Input/Output

### Sample Input (`data/sample_input.csv`):
```csv
id,name,age,salary,bonus,department
1,Alice,25,50000,5000,HR
2,Bob,30,60000,6000,Engineering
3,Charlie,35,70000,7000,Marketing
3,Charlie,35,70000,7000,Marketing
5,David,,80000,8000,Engineering
```

### Sample Output (JSON format returned by Agent):
```json
{
  "result": "The dataset contains 8 observations. There is 1 duplicate row (Charlie, age 35). The column 'age' has the most missing values with 2 null entries.",
  "reasoning": "I inspected table stats showing n_duplicates=1 and p_cells_missing=0.0625. I then reviewed variables for age (n_missing=2) and name (n_missing=1).",
  "recommended_action": "Remove the duplicate row for Charlie, and impute missing ages with the median value (30.0).",
  "citation": "profile.json['table']['n_duplicates'] and profile.json['variables']['age']['n_missing']"
}
```

---

## Assumptions and Limitations
* **Local Parsing**: The context is extracted using direct keyword matching on `profile.json`. Highly unstructured questions or queries referencing values not compiled by ydata-profiling (e.g. deep custom column comparisons) may fall back to general dataset context.
* **Large Datasets**: Very large CSVs will take longer to profile. It is recommended to use minimal mode (which this app does by default) to keep runtimes under a minute.
* **API Limits**: The free tier of Gemini has request rate limits (e.g., 15 RPM).

---

## Demo Steps

1. Start the app: `streamlit run app.py`
2. Ensure the Gemini API Key is configured in the `.env` file.
3. Click "Browse files" under **Upload CSV Dataset** and select `data/Datasets - Telugu movie Dataset.csv`.
4. Click **🚀 Generate Profile Report**. Wait for it to finish.
5. Review the quick summary statistics cards displayed for the uploaded dataset.
6. Click **📥 Download Interactive HTML Report** to verify the static report download.
7. Go to the chat input and ask: *Which column has the most null values?*
8. Inspect the response, expand "Show Logic & Citation", and verify that the reasoning, citation, and recommendations are correct.
9. Ask: *Are there duplicate rows?* and check the result.

---

## Demo Video

Loom Demo Video:
https://www.loom.com/share/91ef824c51a24307b808d410d9be4ea9
