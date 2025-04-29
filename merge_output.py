from pathlib import Path
import json 
import os
from utils import *

output_dir = Path(output_dir)
json_files = list(output_dir.rglob("*.json"))
file_names = list(set([f.stem for f in json_files]))
valid_files = []
for f in file_names:
    all_files = [f for f in output_dir.rglob(f"{f}*.json")]
    if len(all_files) == 3:
        valid_files.append(all_files)
    else:
        print(f"Invalid number of files for {f}: {all_files}")
final_dir = Path(output_dir) / "final"
target_files =  valid_files[0]
for target_files in valid_files:
    main_dict = {}
    file_name = target_files[0].stem
    for f in target_files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            main_dict.update(data)
            
    with open(final_dir / f"{file_name}.json", "w", encoding="utf-8") as file:
        json.dump(main_dict, file, ensure_ascii=False, indent=4)