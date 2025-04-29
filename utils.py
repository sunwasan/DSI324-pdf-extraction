
from google import genai # Import Libraly for Gooogle GenAI SDK
from google.genai import types
from google.genai.errors import APIError

from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
import json
import glob 

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

file_dir = Path(__file__).parent
data_dir = os.path.join(file_dir, "data")
pdf_dir = os.path.join(data_dir, "1_pdf")
instruction_dir = os.path.join(data_dir, "2_instruction")
output_dir = os.path.join(data_dir, "3_output")
all_pdf_paths = glob.glob(os.path.join(pdf_dir, "**", "*.pdf"), recursive=True)

GEMINI_TIMEOUT = 3 * 60 * 1000 # 3 minutes
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT))


def document_description(prompt, pdf_file_path, schema = None):
    if schema:
        config = types.GenerateContentConfig(
            response_schema=schema,
            response_mime_type = "application/json"  
        )  
    else:
        config = types.GenerateContentConfig(
                
            response_mime_type = "application/json"  
        )
              
    with open(pdf_file_path, "rb") as file:
        file_content = file.read()
        
    pdf_content = types.Part.from_bytes(data=file_content, mime_type="application/pdf")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            pdf_content,
            prompt,
        ],
        config=config

    )
    return response.text