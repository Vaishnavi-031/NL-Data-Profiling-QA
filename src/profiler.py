import os
import pandas as pd
from ydata_profiling import ProfileReport
from src.utils import logger, ensure_dirs

def generate_profile_report(csv_path: str, minimal: bool = True) -> tuple[str, str]:
    """
    Generates data profiling reports (HTML and JSON) from a CSV file.
    
    Args:
        csv_path (str): Path to the input CSV file.
        minimal (bool): Whether to run in minimal mode (faster, lighter output). Default is True.
        
    Returns:
        tuple[str, str]: Absolute paths of the generated HTML and JSON reports.
    """
    logger.info(f"Loading dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
        
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded DataFrame with shape: {df.shape}")
    
    _, outputs_dir = ensure_dirs()
    html_output_path = os.path.join(outputs_dir, "profile.html")
    json_output_path = os.path.join(outputs_dir, "profile.json")
    
    logger.info("Starting ydata-profiling generation...")
    # Generate the Profile Report
    profile = ProfileReport(
        df,
        title="Data Profiling Report",
        minimal=minimal,
        explorative=False
    )
    
    # Save to HTML
    logger.info(f"Saving HTML report to: {html_output_path}")
    profile.to_file(html_output_path)
    
    # Save to JSON
    logger.info(f"Saving JSON report to: {json_output_path}")
    profile.to_file(json_output_path)
    
    logger.info("Profiling generation complete!")
    return html_output_path, json_output_path
