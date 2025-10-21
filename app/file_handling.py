from typing import List, Dict
from pydantic import BaseModel
import base64
import mimetypes
import os
import json
import pandas as pd
import sqlite3
import cv2

class Attachment(BaseModel):
    name: str
    url: str




def process_attachments(file_paths):
    """
    Returns:
    - files_text: filename -> text content (for text files)
    - summary: descriptive string about files for LLM prompt
    - files_binary: filename -> bytes content (for images)
    """


    processed_data={}

    for name,file_path in file_paths.items():
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
                
            file_name = name
            file_ext = file_name.split('.')[-1].lower()

            print('file_name :',file_name)
            print('file_ext :',file_ext)
            
            try:
                if file_ext == 'csv':
                    processed_data[file_name] = pd.read_csv(file_path)
                    print(f"Loaded CSV: {file_name} with {len(processed_data[file_name])} rows")
                    
                elif file_ext == 'json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        processed_data[file_name] = json.load(f)
                    print(f"Loaded JSON: {file_name}")
                    
                elif file_ext == 'txt':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        processed_data[file_name] = f.read()
                    print(f"Loaded TXT: {file_name}")

                elif file_ext == 'md':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        processed_data[file_name] = f.read()
                    print(f"Loaded MD: {file_name}")

                elif file_ext in ['xls', 'xlsx']:
                    processed_data[file_name] = pd.read_excel(file_path)
                    print(f"Loaded Excel: {file_name} with {len(processed_data[file_name])} rows")
                    
                elif file_ext == 'parquet':
                    processed_data[file_name] = pd.read_parquet(file_path)
                    print(f"Loaded Parquet: {file_name}")
                    
                elif file_ext == 'db' or file_ext == 'sqlite':
                    conn = sqlite3.connect(file_path)
                    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                    processed_data[file_name] = {}
                    for table_name in tables['name']:
                        processed_data[file_name][table_name] = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
                    conn.close()
                    print(f"Loaded SQLite DB: {file_name}")
                    
                elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                    processed_data[file_name] = cv2.imread(file_path)
                    print(f"Loaded Image: {file_name}")
                    
                elif file_ext == 'pdf':
                    # For PDF processing, we'll generate code to extract text
                    processed_data[file_name] = file_path  # Store path for later processing
                    print(f"Marked PDF for processing: {file_name}")
                    
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                processed_data[file_name] = None

    print('processed_data :',processed_data)
                
    return processed_data