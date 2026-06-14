import os
import streamlit as st
from dotenv import load_dotenv

# Import our modular modules
from src.profiler import generate_profile_report
from src.agent import ProfileAgent
from src.utils import logger, ensure_dirs

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Data Profile Chat",
    page_icon=":material/smart_toy: ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure directories exist
data_dir, outputs_dir = ensure_dirs()

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "profile_generated" not in st.session_state:
    st.session_state.profile_generated = False
if "temp_csv_path" not in st.session_state:
    st.session_state.temp_csv_path = ""
if "json_report_path" not in st.session_state:
    st.session_state.json_report_path = ""
if "html_report_path" not in st.session_state:
    st.session_state.html_report_path = ""
if "stats" not in st.session_state:
    st.session_state.stats = {}

# Sidebar setup
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.write("Configure the prototype settings below:")
    
    if os.getenv("GEMINI_API_KEY"):
        st.success("✅ Gemini API Key loaded from .env")
    else:
        st.error("❌ Gemini API Key not found. Please add it to your .env file.")
        
    st.divider()
    
    st.markdown("""
    ### 💡 Example Questions
    You can ask:
    * *Which column has the most null values?*
    * *Are there duplicate rows in the dataset?*
    * *Which columns are highly correlated?*
    * *What are the major data quality issues?*
    """)
    
    st.divider()
    
    # Reset Chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")

# Main Application Title
st.title(":material/smart_toy: Chat with Data Profiling Reports using AI")
st.write("Upload a CSV, generate a profiling report, and ask questions to inspect data quality, anomalies, and statistics.")

# Step 1: File Upload
st.header("1. Upload CSV Dataset")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    # Save uploaded file to temp path
    temp_path = os.path.join(data_dir, uploaded_file.name)
    
    # If the file has changed, reset state
    if st.session_state.temp_csv_path != temp_path:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.temp_csv_path = temp_path
        st.session_state.profile_generated = False
        st.session_state.chat_history = []
        logger.info(f"New file uploaded and saved to {temp_path}")
        
    st.success(f"Uploaded: **{uploaded_file.name}**")
    
    # Step 2: Report Generation
    st.header("2. Profile Dataset")
    if not st.session_state.profile_generated:
        if st.button("🚀 Generate Profile Report", type="primary", use_container_width=True):
            with st.spinner("Analyzing dataset structure and generating report... This may take up to a minute."):
                try:
                    html_path, json_path = generate_profile_report(temp_path, minimal=True)
                    st.session_state.html_report_path = html_path
                    st.session_state.json_report_path = json_path
                    st.session_state.profile_generated = True
                    
                    # Extract quick overview statistics for the UI cards
                    agent_temp = ProfileAgent(json_path)
                    st.session_state.stats = agent_temp.retriever.get_table_stats()
                    st.success("Profiling report successfully generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate profiling report: {str(e)}")
                    logger.exception("Error in Streamlit profile generation button")
    else:
        st.info("Report has been generated successfully! You can download it or start chatting below.")
        
        # Action Row (Download buttons)
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            try:
                with open(st.session_state.html_report_path, "r", encoding="utf-8") as f:
                    html_data = f.read()
                st.download_button(
                    label="📥 Download Interactive HTML Report",
                    data=html_data,
                    file_name=f"profile_{uploaded_file.name.replace('.csv', '')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            except Exception as e:
                st.error("Error reading HTML report file for download.")
                
        with col_down2:
            try:
                with open(st.session_state.json_report_path, "r", encoding="utf-8") as f:
                    json_data = f.read()
                st.download_button(
                    label="📥 Download Structured JSON Data",
                    data=json_data,
                    file_name=f"profile_{uploaded_file.name.replace('.csv', '')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error("Error reading JSON report file for download.")
        
        # Display Overview Statistics Cards
        st.write("### 📈 Quick Dataset Summary")

        stats = st.session_state.stats
        col1, col2, col3, col4 = st.columns(4)

        p_missing = stats.get('p_cells_missing', 0.0)

        with col1:
            st.metric("Total Rows", stats.get('n_rows', 0))

        with col2:
            st.metric("Columns", stats.get('n_columns', 0))

        with col3:
            st.metric("Missing Cells", f"{p_missing:.2%}")

        with col4:
            st.metric("Duplicate Rows", stats.get('n_duplicates', 0))
            
        # Step 3: Chat Interface
        st.divider()
        st.header("💬 Chat with your Profiling Report")
        
        # Check API key configuration status
        is_key_configured = bool(os.getenv("GEMINI_API_KEY", ""))
        if not is_key_configured:
            st.warning("⚠️ Gemini API Key not found in .env file.")
            
        # Display existing chat messages
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    # Renders structured agent response
                    response_data = message["content"]
                    st.markdown(f"### 🤖 Answer")
                    st.markdown(response_data["result"])
                    
                    with st.expander("🔍 Show Logic & Citation", expanded=True):
                        st.markdown(f"**Reasoning:**\n{response_data['reasoning']}")
                        st.markdown(f"**Recommended Action:**\n{response_data['recommended_action']}")
                        st.markdown(f"**Citation:**")
                        st.code(response_data["citation"])

        # Handle new user input
        if is_key_configured:
            if user_query := st.chat_input("Ask a question about the missing values, duplicates, correlations, or alerts..."):
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.write(user_query)
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                
                # Generate agent response
                with st.chat_message("assistant"):
                    with st.spinner("Retrieving report context and thinking..."):
                        try:
                            # Initialize Agent Core
                            agent = ProfileAgent(
                                json_path=st.session_state.json_report_path,
                                api_key=os.getenv("GEMINI_API_KEY")
                            )
                            response = agent.ask(user_query)
                            
                            # Display answer
                            st.markdown(f"### 🤖 Answer")
                            st.markdown(response["result"])
                            
                            with st.expander("🔍 Show Logic & Citation", expanded=True):
                                st.markdown(f"**Reasoning:**\n{response['reasoning']}")
                                st.markdown(f"**Recommended Action:**\n{response['recommended_action']}")
                                st.markdown(f"**Citation:**")
                                st.code(response["citation"])
                                
                            # Append assistant response to history
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                        except Exception as e:
                            st.error(f"An error occurred while running the agent: {str(e)}")
                            logger.exception("Error in chat execution loop")
else:
    st.info("👋 Upload a CSV file to get started.")
