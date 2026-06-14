import os
import json
from src.utils import logger

class ProfilerRetriever:
    """
    Parses ydata-profiling JSON reports and retrieves relevant sections
    as context for the LLM based on user query keywords.
    """
    
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data = {}
        self.load_report()

    def load_report(self):
        """Loads and parses the JSON profiling report."""
        if not os.path.exists(self.json_path):
            logger.error(f"Profiling JSON not found at {self.json_path}")
            raise FileNotFoundError(f"Profiling JSON not found at {self.json_path}")
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info("Successfully loaded profiling JSON report.")
        except Exception as e:
            logger.error(f"Error loading profiling JSON: {str(e)}")
            raise

    def get_table_stats(self) -> dict:
        """Extracts general table statistics."""
        table = self.data.get("table", {})
        return {
            "n_rows": table.get("n", "N/A"),
            "n_columns": table.get("n_var", "N/A"),
            "n_cells_missing": table.get("n_cells_missing", "N/A"),
            "p_cells_missing": table.get("p_cells_missing", 0.0),
            "n_duplicates": table.get("n_duplicates", "N/A"),
            "p_duplicates": table.get("p_duplicates", 0.0),
        }

    def get_columns_summary(self) -> dict:
        """Extracts summary statistics for each column."""
        variables = self.data.get("variables", {})
        summary = {}
        for col_name, col_data in variables.items():
            col_type = col_data.get("type", "Unknown")
            n_missing = col_data.get("n_missing", 0)
            p_missing = col_data.get("p_missing", 0.0)
            n_distinct = col_data.get("n_distinct", "N/A")
            
            stats = {
                "type": col_type,
                "missing_count": n_missing,
                "missing_percentage": f"{p_missing:.2%}" if isinstance(p_missing, (int, float)) else "N/A",
                "distinct_count": n_distinct
            }
            
            # Add numeric stats if applicable
            if "mean" in col_data:
                stats["mean"] = round(col_data["mean"], 4)
            if "min" in col_data:
                stats["min"] = col_data["min"]
            if "max" in col_data:
                stats["max"] = col_data["max"]
                
            summary[col_name] = stats
        return summary

    def get_alerts(self) -> list:
        """Extracts data quality warnings/alerts."""
        alerts_raw = self.data.get("alerts", [])
        alerts = []
        for alert in alerts_raw:
            if isinstance(alert, str):
                alerts.append(alert)
            elif isinstance(alert, dict):
                # If ydata-profiling uses a dict format for alerts
                alert_type = alert.get("type", "")
                column = alert.get("column", "")
                message = f"Alert for '{column}': {alert_type}"
                alerts.append(message)
        return alerts

    def get_correlations_summary(self) -> list:
        """Extracts highly correlated variables from alerts."""
        alerts = self.get_alerts()
        correlations = []
        for alert in alerts:
            alert_lower = alert.lower()
            if "correlat" in alert_lower:
                correlations.append(alert)
        return correlations

    def retrieve_context(self, question: str) -> str:
        """
        Retrieves relevant profiling context based on keyword matching.
        
        Args:
            question (str): The user's query.
            
        Returns:
            str: Markdown formatted context string.
        """
        q_lower = question.lower()
        table_stats = self.get_table_stats()
        cols_summary = self.get_columns_summary()
        alerts = self.get_alerts()
        
        context_parts = []
        
        # 1. Identify specific columns mentioned in the query
        columns_mentioned = [col for col in cols_summary.keys() if col.lower() in q_lower]
        
        # 2. Match general keywords
        is_missing_query = any(k in q_lower for k in ["missing", "null", "empty", "na", "nan"])
        is_duplicate_query = any(k in q_lower for k in ["duplicate", "identical", "repeat"])
        is_correlation_query = any(k in q_lower for k in ["correlat", "relation", "depend"])
        is_alert_query = any(k in q_lower for k in ["alert", "warn", "issue", "quality", "problem"])
        
        # Always include high-level summary metadata
        context_parts.append("### Dataset Overview")
        context_parts.append(f"- Number of Rows: {table_stats['n_rows']}")
        context_parts.append(f"- Number of Columns: {table_stats['n_columns']}")
        context_parts.append(f"- Duplicate Rows: {table_stats['n_duplicates']} (Percentage: {table_stats['p_duplicates']:.2%})")
        context_parts.append(f"- Total Missing Cells: {table_stats['n_cells_missing']} (Percentage: {table_stats['p_cells_missing']:.2%})")
        
        # Add column-specific contexts if mentioned
        if columns_mentioned:
            context_parts.append("\n### Detailed Variable Information for Mentioned Columns")
            for col in columns_mentioned:
                info = cols_summary[col]
                info_str = f"**Column: '{col}'** (Type: {info['type']})\n"
                info_str += f"  - Missing: {info['missing_count']} ({info['missing_percentage']})\n"
                info_str += f"  - Distinct Values: {info['distinct_count']}\n"
                if "mean" in info:
                    info_str += f"  - Mean: {info['mean']} | Min: {info['min']} | Max: {info['max']}\n"
                context_parts.append(info_str)
                
        # Add missing values details if requested
        if is_missing_query:
            context_parts.append("\n### Missing Values Breakdown per Column")
            for col, info in cols_summary.items():
                if info['missing_count'] > 0:
                    context_parts.append(f"- Column '{col}': {info['missing_count']} missing values ({info['missing_percentage']})")
            if not any(info['missing_count'] > 0 for info in cols_summary.values()):
                context_parts.append("- No missing values found in any column.")
                
        # Add duplicates details if requested
        if is_duplicate_query:
            context_parts.append("\n### Duplicate Records Information")
            context_parts.append(f"- Duplicate Rows Count: {table_stats['n_duplicates']}")
            context_parts.append(f"- Duplicate Rows Percentage: {table_stats['p_duplicates']:.2%}")
            
        # Add correlation details if requested
        if is_correlation_query:
            context_parts.append("\n### Highly Correlated Columns")
            corrs = self.get_correlations_summary()
            if corrs:
                for corr in corrs:
                    context_parts.append(f"- {corr}")
            else:
                context_parts.append("- No severe high correlation warnings found in ydata-profiling alerts.")
                
        # Add alerts if requested or if it's a general question
        if is_alert_query or (not columns_mentioned and not is_missing_query and not is_duplicate_query and not is_correlation_query):
            context_parts.append("\n### Data Quality Warnings / Alerts")
            if alerts:
                for alert in alerts:
                    context_parts.append(f"- {alert}")
            else:
                context_parts.append("- No data quality alerts or warnings generated.")
                
        # If it's a general overview question, also add the column list
        if not columns_mentioned and not is_missing_query and not is_duplicate_query and not is_correlation_query and not is_alert_query:
            context_parts.append("\n### Columns List and Types")
            for col, info in cols_summary.items():
                context_parts.append(f"- Column '{col}': Type {info['type']}")
                
        return "\n".join(context_parts)
