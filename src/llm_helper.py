import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from src.utils import logger

# Load environment variables (useful if GEMINI_API_KEY is defined in .env)
load_dotenv()

class GeminiHelper:
    """
    Interfaces with Google's Gemini API to query dataset profile report context
    and return structured analysis responses.
    """
    
    def __init__(self, api_key: str = None):
        # Allow key to be passed from UI, fallback to environment variable
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-2.5-flash"
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            logger.info("Gemini API client configured successfully.")
        else:
            logger.warning("Gemini API key is not configured. API calls will fail until configured.")

    def is_configured(self) -> bool:
        """Returns True if the API key is set."""
        return bool(self.api_key)

    def set_api_key(self, api_key: str):
        """Sets/updates the API key at runtime."""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        logger.info("Gemini API key updated at runtime.")

    def query_profile(self, question: str, context: str) -> dict:
        """
        Sends the user question and retrieved context to Gemini and gets a structured JSON response.
        
        Args:
            question (str): User's natural language question.
            context (str): Retrieved context block from the profile JSON.
            
        Returns:
            dict: Structured response matching the desired output schema.
        """
        if not self.is_configured():
            return {
                "result": "Gemini API key is missing.",
                "reasoning": "The application could not connect to Gemini because no API key was provided.",
                "recommended_action": "Please enter your Gemini API key in the sidebar or save it in a .env file.",
                "citation": "System configuration"
            }
            
        system_instruction = (
            "You are an expert data analyst assistant. Your job is to answer questions about a dataset "
            "based ONLY on the provided ydata-profiling report context. "
            "You must return your response as a valid JSON object with the following structure:\n"
            "{\n"
            '  "result": "A clear, concise, direct answer to the user\'s question. Reference specific numbers or facts.",\n'
            '  "reasoning": "Step-by-step logic explaining how you arrived at the answer using the context.",\n'
            '  "recommended_action": "A concrete data-cleaning or analytical recommendation based on the finding.",\n'
            '  "citation": "The exact metric, column name, or warning alert from the context where the information came from."\n'
            "}\n"
            "Ensure the output contains no markdown formatting outside of the JSON block. Do not wrap the JSON in ```json...```."
        )
        
        prompt = (
            f"Here is the context extracted from the data profiling report:\n"
            f"-----------------\n"
            f"{context}\n"
            f"-----------------\n"
            f"User Question: {question}\n\n"
            f"Answer the question using the context. Follow the requested JSON format strictly."
        )

        try:
            logger.info("Invoking Gemini model...")
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            
            # Using JSON response mime type to force structured output
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text.strip()
            logger.info("Received response from Gemini.")
            
            # Parse the response
            parsed_response = self._parse_json_response(response_text)
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return {
                "result": "Error communicating with Gemini API.",
                "reasoning": f"An exception occurred: {str(e)}",
                "recommended_action": "Verify your API key is valid and you have internet access.",
                "citation": "Gemini SDK Error"
            }

    def _parse_json_response(self, text: str) -> dict:
        """Helper to safely parse JSON from the response text."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback regex in case it wrapped it in markdown code blocks
            logger.warning("JSON parsing failed direct conversion. Attempting regex extraction...")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # If all fails, return a manual structure wrapping the text
            return {
                "result": "Failed to parse structured JSON from LLM response.",
                "reasoning": f"Raw output: {text[:200]}...",
                "recommended_action": "Try rephrasing the question or checking API limits.",
                "citation": "Response parser"
            }
