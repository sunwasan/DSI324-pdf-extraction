# from template import template
from utils import *
import json 
from pathlib import Path


template = """
You are a data extraction assistant. Your task is to extract data from a PDF document according to the specific instructions provided.  
You must extract all specified keys and return the results in properly formatted, valid **JSON**.

**loc**: Refers to the heading number or title in the PDF from which you should extract the content.  
For example:  
- `4.3.2.4` means the content under the heading labeled `4.3.2.4`.  
- `คำอธิบายรายวิชา` means the content under the heading titled `คำอธิบายรายวิชา`.

Extraction Instructions (**FOR YOUR UNDERSTANDING ONLY — DO NOT copy into your output**):  
{json_instruction}

**Important Output Rules:**  
- Your final output must be a valid, properly formatted **JSON** object.  
- Fill all fields as instructed.  
- If a field is missing in the source, set its value to an empty string (`""`) or an appropriate default value based on the expected type.

Example format (for reference only — DO NOT include in your output):
```json
{{
    "professor": [
        {{
            "lecture-position": "ผู้ช่วยศาสตราจารย์",
            "lecture-first-name": "พัฒนกิจ",
            "lecture-last-name": "ชอบทำกิจ",
            "bachelor-degree": "ศศ.บ.",
            "doctor-degree": "Ph.D.",
            "bachelor-institute": "มหาวิทยาลัยธรรมศาสตร์",
            "doctor-institute": "University of Kent, UK",
            "doctor-graduate-year": "2564",
            "bachelor-graduate-year": "2551"
        }},
        {{
            "lecture-position": "ผู้ช่วยศาสตราจารย์",
            "lecture-first-name": "วรวัชร์",
            "lecture-last-name": "ตั้งจิตรเจริญ",
            "bachelor-degree": "ศศ.บ.",
            "doctor-degree": "Ph.D.",
            "bachelor-institute": "มหาวิทยาลัยธรรมศาสตร์",
            "doctor-institute": "Aarhus University, Denmark",
            "doctor-graduate-year": "2564",
            "bachelor-graduate-year": "2552"
        }},
        ...
    ]
}}
"""         

def extract_courses(pdf_file_path, load:bool = False, retries = 5):
    
    instruction_included = ['courses']
    output_dir = os.path.join(data_dir, "3_output", 'courses')
    instruction_included = [s + '.json' for s in instruction_included]
    instructions = {}
    file_name = Path(pdf_file_path).stem
    output_file = os.path.join(output_dir, f"{file_name}.json")
    if not load and os.path.exists(output_file):
        print(f"Output file already exists: {output_file}")
        return
    
    for file in os.listdir(instruction_dir):
        if file.endswith('.json') and file in instruction_included:
            with open(os.path.join(instruction_dir, file), 'r', encoding='utf-8') as f:
                instructions.update(json.load(f))
    try:
        prompt = template.format(json_instruction=json.dumps(instructions, ensure_ascii=False))
        tries = 0
        while tries < retries:
            try:
                r = document_description(prompt, pdf_file_path)
                r_json = r[r.find("{"):r.rfind("}")+1]
                r_json = json.loads(r_json)
                file_name = Path(pdf_file_path).stem
                if len(r_json) == 0:
                    raise ValueError("No courses found")
                output_file = os.path.join(output_dir, f"{file_name}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(r_json, f, ensure_ascii=False, indent=4)
                break
            except Exception as e:
                print(f"Retrying due to error: {e}")
                tries += 1
                if tries >= retries:
                    raise e
            
    except Exception as e:
        
        print(f"Error processing {pdf_file_path}: {e}")

def extract_professor(pdf_file_path, load:bool = False, retries = 5):
    tries = 0
    
    instruction_included = ['professors']
    output_dir = os.path.join(data_dir, "3_output", 'professors')
    instruction_included = [s + '.json' for s in instruction_included]
    instructions = {}
    file_name = Path(pdf_file_path).stem
    output_file = os.path.join(output_dir, f"{file_name}.json")
    if not load and os.path.exists(output_file):
        print(f"Output file already exists: {output_file}")
        return
    
    for file in os.listdir(instruction_dir):
        if file.endswith('.json') and file in instruction_included:
            with open(os.path.join(instruction_dir, file), 'r', encoding='utf-8') as f:
                instructions.update(json.load(f))
    try:
        prompt = template.format(json_instruction=json.dumps(instructions, ensure_ascii=False))
        while tries < retries:
            try:
                r = document_description(prompt, pdf_file_path)
                r_json = r[r.find("{"):r.rfind("}")+1]
                r_json = json.loads(r_json)
                if len(r_json) == 0:
                    raise ValueError("No professors found")
                

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(r_json, f, ensure_ascii=False, indent=4)
                break
            except Exception as e:
                print(f"Retrying due to error: {e}")
                tries += 1
                if tries >= retries:
                    raise e
                

    except Exception as e:
        
        print(f"Error processing {pdf_file_path}: {e}")
def extract_courses_and_professor(pdf_file_path, load:bool = False):
    # extract_courses(pdf_file_path, load)
    extract_professor(pdf_file_path, load)
from tqdm import tqdm
if __name__ == "__main__":
    for pdf in tqdm(all_pdf_paths):
        extract_courses_and_professor(pdf, load=False)