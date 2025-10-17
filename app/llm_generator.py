import openai
import pandas as pd
import numpy as np
import csv
import io
import os
from dotenv import load_dotenv
from file_handling import process_attachments
import cv2
import pytesseract
import requests

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_url='https://aipipe.org/openai/v1/chat/completions'

def generate_app_code(brief, file_paths,image_present,image_data):

    use_mock=False
    if use_mock:
        print("Sending the mock llm response")
        html=f"<html><body><h1>Mock App for : {brief} </h1><img src='sample.png'ī /></body></html>"
        return {
            "index.html":html.encode('utf-8')
        }
    
    if file_paths:
    
        print("Starting to process attachments")
        file_info = process_attachments(file_paths)
        print("Received processed attachments")

        print('file info :',file_info)

        # Build attachment info snippet for the prompt
        data_description = {}

        for filename, data in file_info.items():
                if isinstance(data, pd.DataFrame):
                    data_description[filename] = {
                        "type": "DataFrame",
                        "shape": data.shape,
                        "columns": list(data.columns),
                        "sample": data.head(3).to_dict(orient="records")
                    }
                elif isinstance(data, dict):
                    data_description[filename] = {
                        "type": "Dictionary",
                        "keys": list(data.keys()) if data else []
                    }
                elif isinstance(data, list):
                    data_description[filename] = {
                        "type": "List",
                        "length": len(data),
                        "sample": data[:2] if len(data) > 0 else []
                    }
                elif isinstance(data, str):
                    data_description[filename] = {
                        "type": "String",
                        "length": len(data),
                        "sample": data if len(data) <= 200 else data[:200] + "..."
                    }
                elif isinstance(data, np.ndarray):
                    try:
                        # Preprocess image for OCR
                        gray = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
                        blur = cv2.GaussianBlur(gray, (5, 5), 0)
                        thresh = cv2.adaptiveThreshold(
                            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY_INV, 11, 2
                        )

                        # Run OCR
                        custom_config = r'--oem 3 --psm 6'
                        ocr_text = pytesseract.image_to_string(thresh, config=custom_config)

                        data_description[filename] = {
                            "type": "Image",
                            "ocr_text_sample": ocr_text if len(ocr_text) <= 200 else ocr_text[:200] + "...",
                            "info": "OCR processed with Tesseract"
                        }

                    except Exception as e:
                        data_description[filename] = {
                            "type": "Image",
                            "error": "Available for processing"
                        }


                else:
                    data_description[filename] = {
                        "info": "Available for processing"
                    }

    
    else:
        data_description="None"
    
    print("Finished creating data description")
    print("data_description:", data_description)





    prompt = f"""Build a minimal web app for this brief: {brief} 
    A Sample of the Attachments (may be needed in the app logic or UI):{data_description}
    Use the sample only to understand the structure/format.
    The full attachment files will be available in the same directory as index.html, and should be fetched via JavaScript on page load.
    Do not require the user to trigger a fetch unless the brief requires interactivity.
    Return ONLY the complete content of a single file named 'index.html' as plain text with no explanations. Do NOT return any JSON or additional files. Include all necessary HTML, CSS, and JavaScript inline.
    If external libraries are used, load them correctly and ensure to use the latest stable versions to generate up-to-date, working code.
    Make sure the code has NO syntax errors."""

    print("Final prompt:",prompt)

    try:


        print("Sending the llm prompt")

      

        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer{api_key}"
        }

        if image_present==True:
            content=[{ "type": "text", "text": prompt }]
            for i in image_data:
                content.append({"type": "image_url","image_url": {"url":i['url']}})
                
            data={
                "model": "gpt-5-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": content     
                        
                    }
                ],    
            }
            print("Inside image version of the model request",flush=True)
            print("content:",content)

        else:
            data={
                "model": "gpt-5-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],   
            }
            print("Inside non-image version of the model request",flush=True)
            
        
        response=requests.post(api_url, headers=headers, json=data)
        if response.status_code==200:
            code = response.json().get('choices',[])[0].get('message',{}).get('content',"")

            return code
        else:
            print(f"Error {response.status_code}: {response.text}")
            MINIMAL_HTML="""<!DOCTYPE html>
            <html><head><title>Fallback App</title></head><body><h1>The fallback app for the task</h1></body></html>"""
            code = MINIMAL_HTML
            return code


    except:
        print("OpenAI error",flush=True)
        print("Status code:", response.status_code)
        print("Reason:", response.reason)
        print("Response body:", response.text)  # raw response
        MINIMAL_HTML="""<!DOCTYPE html>
        <html><head><title>Fallback App</title></head><body><h1>Failed to generate app</h1></body></html>"""
        code = MINIMAL_HTML
        return code


def revise_app_code(brief, file_paths, html_content,image_present,image_data,repo_url,first_brief):

    use_mock=False
    if use_mock:
        print("Sending the mock llm response")
        html=f"<html><body><h1>Mock App for : {brief} </h1><h3>Modified second round of requests</h3></body></html>"
        return html


    #files_text, summary, files_binary = process_attachments(attachments)



    if file_paths:
    
        print("Starting to process attachments")
        file_info = process_attachments(file_paths)
        print("Received processed attachments")

        # Build attachment info snippet for the prompt
        data_description = {}

        for filename, data in file_info.items():
                if isinstance(data, pd.DataFrame):
                    data_description[filename] = {
                        "type": "DataFrame",
                        "shape": data.shape,
                        "columns": list(data.columns),
                        "sample": data.head(3).to_dict(orient="records")
                    }
                elif isinstance(data, dict):
                    data_description[filename] = {
                        "type": "Dictionary",
                        "keys": list(data.keys()) if data else []
                    }
                elif isinstance(data, list):
                    data_description[filename] = {
                        "type": "List",
                        "length": len(data),
                        "sample": data[:2] if len(data) > 0 else []
                    }
                elif isinstance(data, str):
                    data_description[filename] = {
                        "type": "String",
                        "length": len(data),
                        "sample": data if len(data) <= 200 else data[:200] + "..."
                    }
                elif isinstance(data, np.ndarray):
                    try:
                        reader = easyocr.Reader(['en'])
                        # Preprocess image for OCR
                        gray = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
                        blur = cv2.GaussianBlur(gray, (5, 5), 0)
                        thresh = cv2.adaptiveThreshold(
                            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY_INV, 11, 2
                        )

                        result = reader.readtext(thresh)
                        # Extract just text parts and join them
                        ocr_text = " ".join([res[1] for res in result])

                        data_description[filename] = {
                            "type": "Image",
                            "ocr_text_sample": ocr_text if len(ocr_text) <= 200 else ocr_text[:200] + "...",
                            "info": "OCR processed with Easyocr"
                        }

                    except Exception as e:
                        data_description[filename] = {
                            "type": "Image",
                            "error": f"OCR failed: {str(e)}"
                        }
                else:
                    data_description[filename] = {
                        "type": type(data).__name__,
                        "info": "Available for processing"
                    }

    
    else:
        data_description="None"
    
    print("Finished creating attachment_info")
    print("attachment_info:", data_description)
  

    
    prompt = f"""
    You previously generated a minimal web app with the following brief: "{first_brief}"
    Here is a sample of the index.html file generated:
    {html_content} 
    Now, update only the index.html file by incorporating the new requirements below, while still respecting the original brief and structure:
    "{brief}"
    A Sample of the Attachments (may be needed in app logic or UI):
    {data_description}
    The entire attachment will be in the same directory as the index.html file available through Javascript fetch requests.
    Return ONLY the complete content of a single file named 'index.html' as plain text with no explanations. Do NOT return any JSON or additional files. Include all necessary HTML, CSS, and JavaScript inline.
    If external libraries are used, use the latest stable versions to generate up-to-date, working code. 
    **DO NOT use deprecated syntax.**
    Always use jsDelivr to load external libraries unless the brief explicitly instructs otherwise.
    Ensure all JavaScript regex literals are syntactically valid. 
    For splitting text by lines, use ONLY **text.split(/\r?\n/)** IF REQUIRED.
    IF marked library is used, DO NOT use marked() 
    Make sure the code has NO syntax errors."""


    print("prompt:",prompt)

    try:
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer{api_key}"
        }
    
        if image_present==True:
            content=[{ "type": "text", "text": prompt }]
            for i in image_data:
                content.append({"type": "image_url","image_url": {"url":i['url']}})
                
            data={
                "model": "gpt-5-nano",
                "messages": [
                    {
                        "role": "user",
                        "content": content     
                        
                    }
                ], 
            }

        else:
            data={
                "model": "gpt-5-nano",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],  
            }
    
        response=requests.post(api_url, headers=headers, json=data)
        if response.status_code==200:
            code = response.json().get('choices',[])[0].get('message',{}).get('content',"")
    
            return code
        else:
            code="""<!DOCTYPE html>
            <html><head><title>Fallback App</title></head><body><h1>The fallback app for round-2</h1></body></html>"""
            return code

    except:
        code="""<!DOCTYPE html>
        <html><head><title>Fallback App</title></head><body><h1>Failed to generate app for round-2</h1></body></html>"""
        return code
