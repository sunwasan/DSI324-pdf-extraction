from template import template
from utils import *
from tqdm import tqdm
from pydantic import BaseModel
from typing import List, Dict, Optional
import time

instruction_included = ['section1', 'section2', 'section3', 'section4']
instruction_included = [s + '.json' for s in instruction_included]
instructions = {}
for file in os.listdir(instruction_dir):
    if file.endswith('.json') and file in instruction_included:
        with open(os.path.join(instruction_dir, file), 'r', encoding='utf-8') as f:
            instructions.update(json.load(f))

max_retries = 5
output_keys = list(instructions.keys())
prompt = template.format(json_instruction=json.dumps(instructions, ensure_ascii=False), output_keys=f'{output_keys}')

output_dir = os.path.join(data_dir, "3_output", 'basic_info') 
os.makedirs(output_dir, exist_ok=True)   
    
def extract_basic_info(pdf_file_path, load: bool = False):
    file_name = Path(pdf_file_path).stem
    output_file = os.path.join(output_dir, f"{file_name}.json")
    if not load and os.path.exists(output_file):
        print(f"File {output_file} already exists. Skipping...")
        return

    
    for attempt in range(1, max_retries + 1):
        try:
            r = document_description(prompt, pdf_file_path)
            r_json = r[r.find("{"):r.rfind("}")+1]
            r_json = json.loads(r_json)
            if len(r_json) == 0:
                print(f"Empty response for {pdf_file_path}.")
                return
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(r_json, f, ensure_ascii=False, indent=4)
            return r_json
        
        except Exception as e:
            print(f"Attempt {attempt}/{max_retries} failed for {pdf_file_path}: {e}")
            if attempt < max_retries:
                time.sleep(1)  # optional: small delay before retrying
            else:
                print(f"Failed to process {pdf_file_path} after {max_retries} attempts.")

def extract_all_basic_info(load: bool = False):
    for pdf_file_path in tqdm(all_pdf_paths):
        extract_basic_info(pdf_file_path, load)

if __name__ == "__main__":
    extract_all_basic_info(load=False)
