import os
import logging

def setup_logging():
    """Set up basic logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger("data_profiler_chat")

logger = setup_logging()

def ensure_dirs():
    """Ensure that the data and outputs directories exist."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_dir, "data")
    outputs_dir = os.path.join(project_dir, "outputs")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    
    return data_dir, outputs_dir
