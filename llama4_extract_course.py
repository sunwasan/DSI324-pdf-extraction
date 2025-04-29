import re
import json
from pathlib import Path
from collections import defaultdict
from openai import OpenAI
import numpy as np
import pandas
import fitz

from fixthaipdf import clean
from template import template
from utils import *
from tqdm import tqdm

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

course_instruction_path = os.path.join(file_dir,'data','2_instruction','courses.json')
with open(course_instruction_path, 'r', encoding='utf-8') as f:
    course_instruction = json.load(f)
    
prompt_template = """
You are a highly skilled data extraction model specializing in extracting structured information from text and formatting it as a JSON object.

Your task is to extract specific details about a course from the provided text.
Follow the schema and extraction rules below to identify and extract the relevant information for each key.
Present the extracted data as a single JSON object.
If a field is not found in the text, set its value to default value based on result type.

Extraction Schema and Rules:
{course_instruction}

Text to Process:
{text}



Output JSON:
"""
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

from gemini_extract_course import extract_course_description

def extract_course_desc(course_desc):
    try:
        formated_prompt = prompt_template.format(text=course_desc, course_instruction=course_instruction)
        response = client.chat.completions.create(
            temperature=0.1,
            model="meta-llama/llama-4-scout:free",
            messages=[{"role": "user", "content": formated_prompt}]
        )
        
        response_text = response.choices[0].message.content
        response_json = response_text[response_text.find("{"):response_text.rfind("}")+1]
        response_json = json.loads(response_json)
        return response_json
    except Exception as e:
        print(f"Error: {e}")
        return None

def extract_courses(pdf_file_path:str, load:bool = False) -> list:
    file_name = str(Path(pdf_file_path).name)
    file_name = file_name.replace('.pdf', '')

    output_dir = os.path.join(data_dir, "3_output", 'courses')
    output_file = os.path.join(output_dir, f"{file_name}.json")
    
    if not load and os.path.exists(output_file):
        print(f"Output file already exists: {output_file}")
        return
    
    courses = extract_course_description(pdf_file_path)
    
    if len(courses) == 0:
        print(f"No courses found in {pdf_file_path}.")
        return
    
    all_courses = []
    for course in tqdm(courses):
        course_desc = extract_course_desc(course)
        if course_desc:
            all_courses.append(course_desc)
    all_courses_json = {"courses": all_courses}
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_courses_json, f, ensure_ascii=False, indent=4)
        
if __name__ == "__main__":
    extract_courses(r"C:\Users\User\workspace\DSI324_PDF_Extract\data\1_pdf\คณะสถาปัตยกรรมศาสตร์และการผังเมือง\BLN66-ภูมิสถาปัตยกรรมบัณฑิต66-สภาฯ25-4-66-อว.P\สำเนาของ 4-ภูมิสถาปัตยกรรมบัณฑิต2566-P.pdf", load=False)