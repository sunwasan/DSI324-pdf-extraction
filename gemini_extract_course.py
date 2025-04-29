import re
import json
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas
import fitz

from fixthaipdf import clean
from template import template
from utils import *
from tqdm import tqdm

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

with open(os.path.join(data_dir, "2_instruction", "courses.json"), 'r', encoding='utf-8') as f:
    intruction_json = json.load(f)

def clean_text(text):
    unicode_box_dict = {
        "\uf0fe" : "\n<include>",
        "\uf052" : "\n<include>",
        "\uf06f" : "\n<exclude>",
        "\uf0a3" : "\n<exclude>",
        
    }
    for unicode_box, replacement in unicode_box_dict.items():
        text = text.replace(unicode_box, replacement)
    
    text = clean(text)    
    return text

def get_course_description_lines(doc) -> list:
    start_page = 0
    end_page = 0
    page_lines = []
    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            text_dict = page.get_text("dict")
            text_blocks = text_dict["blocks"]
            if not any(block.get("type") == 0 for block in text_blocks):
                pass        
            for block in text_blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        y = np.floor(span["bbox"][1])  # use rounded y to group lines
                        font = span["font"]
                        font = 'bold' if 'bold' in font.lower() else 'normal'
                        clean_txt = clean_text(span["text"])
                        if 'สารบัญ' in clean_txt:
                            continue
                        if 'อธิบายรายวิชา' in clean_txt and font == 'bold':
                            start_page = page_num
                            
                        if start_page > 0:
                            if 'หมวดที่' in clean_txt and page_num > start_page and font == 'bold':
                                end_page = page_num
                                continue
                            elif re.search(r"(\d+\.\d+)\s+(.+)", clean_txt) and font == 'bold' and page_num > start_page:
                                end_page = page_num
                                continue
                            else:
                                page_lines.append( (clean_txt , font))                             
            if start_page > 0 and end_page > 0:
                break     
        except Exception as e:
            print(f"Error processing page {page_num}: {e}") 
    return page_lines


def extract_course_description(pdf_file_path:str) -> list:
    file_name = str(Path(pdf_file_path).name)
    file_name = file_name.replace('.pdf', '')

    doc = fitz.open(pdf_file_path)  # Open the PDF


    
    course_pattern = r'^[ก-๙]+\s?\.?\s*[0-9]{3}.*$'
    courses = []
    prev_course = None
    course_txt = ''
    
    kw = ['บังคับ', 'ทั่วไป', 'เลือก', 'เสรี']
    prev_type = None
    
    course_description_lines = get_course_description_lines(doc)
    course_description_lines = [l for l in course_description_lines if l[0] != '']
    
    for i, line in enumerate(course_description_lines):
        txt = line[0]
        font = line[1]
        
        if font == 'bold' and any( kw in txt for kw in kw):
            prev_type = txt    
        
        if re.match(course_pattern, txt):
            if prev_course:
                courses.append(course_txt)
                prev_course = None
            course_txt = '<course-type>' + prev_type + '</course-type>' + '\n'
            course_txt += txt + '\n'
            prev_course = txt
        else:
            if prev_course:
                course_txt += txt + '\n'
    return courses
    
def extract_course_desc(course_desc):
    try:
        formated_prompt = prompt_template.format(text=course_desc, course_instruction=intruction_json)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                formated_prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type = "application/json" 
            )
        )
        return json.loads(response.text)
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
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=4)
        