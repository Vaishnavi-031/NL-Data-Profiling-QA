# AI Usage Note

This document details how AI assisted in the development of the "Chat with Data Profiling Reports using AI" prototype.

## How AI Helped During Development
1. **Architecture & Project Layout**: Codebase structure, separating responsibilities into modular source files (`src/profiler.py`, `src/retrieval.py`, `src/llm_helper.py`, `src/agent.py`), and a frontend driver `app.py`.
2. **Context-Retrieval Strategy**: Developed a lightweight keyword-based context retriever from the generated `profile.json` to keep the context clean and avoid third-party vector index libraries (e.g. FAISS).
3. **Structured JSON Enforcement**: Crafted system instructions paired with Gemini's native `"response_mime_type": "application/json"` config parameter, ensuring structured schema output without markdown code block wrapping.
4. **Citation Validation**: Implemented custom Python logic in the Agent layer to crosscheck the generated citation strings against columns, statistics, and alerts parsed from the profiling report.
5. **Robust Mock Testing**: Written a pytest suite using `unittest.mock` to mock Gemini calls and test edge cases, including missing key recovery and unverified citation tagging.

## What AI Got Wrong / Corrections Made
1. **Initial Vector Search Proposal**: The initial plan included FAISS. Upon refinement, we recognized that a simple keyword/string match on the structured ydata-profiling JSON was far simpler, more lightweight, and fully resolved the requirements without additional complexity.
2. **HTML Embedding**: Initially, the plan suggested embedding the HTML profile in an iframe. Since nested iframes can make Streamlit pages laggy or cause scroll nesting issues, we replaced it with direct, clean download buttons for the generated `profile.html` and `profile.json` files.
3. **Environment/Workspace Paths**: Corrected folder creation paths to respect local Windows filesystem structures and sandbox limits, saving artifacts and data securely.

## Best Prompts Used
* **System Prompt for Output Schema**: Specifying a clear JSON template inside the `system_instruction` parameter of `genai.GenerativeModel`, combined with `response_mime_type="application/json"` configuration, led to 100% compliant responses.
* **Keyword Matching Retrieval Logic**: Writing a prompt to request modular Python code that maps question intents (like missing, duplicates, correlations, alerts) directly to corresponding keys in the `profile.json` structure, allowing lightweight extraction of data summaries.

## Human Review
All AI-generated suggestions were reviewed and tested by our team before being included in the final prototype.