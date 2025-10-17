from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config import SERVER_SECRET
from github_utils import create_repo, enable_github_pages, push_code
from llm_generator import generate_app_code,revise_app_code
from file_handling import process_attachments
from evaluator import notify_evaluator
from mit_license import generate_mit_license
from readme import generate_readme
import tempfile
import os
from dotenv import load_dotenv
import base64
import re 
import sys 
from bs4 import BeautifulSoup
import requests
import shutil

app=FastAPI()

load_dotenv()

class AppRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    evaluation_url: str
    checks: list = []
    attachments: list = []

SERVER_SECRET=os.getenv("SERVER_SECRET")
GITHUB_TOKEN=os.getenv("GITHUB_TOKEN")

@app.post("/api-endpoint")
async def api_handler(req:AppRequest,background_tasks:BackgroundTasks):
    print(SERVER_SECRET)
    if req.secret != SERVER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    print("Successfully validated the server secret")

    print("Started background task")
    background_tasks.add_task(process_request, req)

    print("Returned the immediate 200 Ok response")
    return JSONResponse(content={"status":"received"},status_code=200)

repo_store = {}

def process_request(req:AppRequest):
    print("process_request has been invoked") 
    try:
        if req.round == 1:

            print("Started the llm request",flush=True)

            if req.attachments:
                image_present=False

                #save the files 
                upload_dir = "/tmp"
                file_paths = {}
                image_data=[]

                for dict in req.attachments:
                    if dict['url'].startswith("data:image/"):
                        image_present=True
                        image_data.append({'url':dict['url']})
                    filepath = os.path.join(upload_dir, dict['name'])
                    _, base64_data = dict['url'].split(",", 1)
                    decoded_bytes = base64.b64decode(base64_data)
                    with open(filepath, "wb") as f:
                        f.write(decoded_bytes)

                file_paths[dict['name']]=filepath

                print("Saved files")

                print("file_paths :",file_paths)

                print("Sending brief with attachments",flush=True)

                files = generate_app_code(req.brief,file_paths,image_present,image_data)

                print(files,flush=True)
                print("Received the response from the llm")
                # print(req.attachments)
                #files_text, summary, files_binary = process_attachments(req.attachments)
            else:
                print("Sending brief without attachments")
                files=generate_app_code(req.brief,None,image_present=False,image_data=[])
                print("Received the response from the llm")
                #files_txt,summary,files_binary=None,None,None

            print("Starting the temp directory",flush=True)
            # with tempfile.TemporaryDirectory() as temp_dir:
            #     for name, content in files.items():
            #         filepath = os.path.join(temp_dir, name)
            #         os.makedirs(os.path.dirname(filepath), exist_ok=True)
            #         with open(filepath, "wb") as f:
            #             f.write(content)



            def extract_html_from_llm_response(response: str) -> str:
                """
                Extracts the HTML code inside markdown ```html fences from an LLM response,
                removes any explanation text before or after, and returns clean HTML.
                If no markdown fences found, tries to locate the first <!DOCTYPE and returns from there.
                Args:
                    response (str): Raw LLM response string.
                Returns:
                    str: Cleaned HTML string starting with <!DOCTYPE.
                Raises:
                    ValueError: if no HTML code found.
                """

                response = response.strip()

                # 0. Early return: Check if response is already valid HTML
                if re.match(r"^(<!DOCTYPE|<html)", response, re.IGNORECASE):
                    return response



                # 1. Try to extract content inside ```html ... ```
                fence_pattern = re.compile(r"```html\s*(.*?)```", re.DOTALL | re.IGNORECASE)
                match = fence_pattern.search(response)
                if match:
                    html_code = match.group(1).strip()
                    # Confirm it starts with <!DOCTYPE or <html>
                    if re.match(r"^(<!DOCTYPE|<html)", html_code, re.IGNORECASE):
                        return html_code

                # 2. Fallback: find first <!DOCTYPE in entire response and return from there
                doctype_match = re.search(r"<!DOCTYPE", response, re.IGNORECASE)
                if doctype_match:
                    html_code = response[doctype_match.start():].strip()
                    # Cut off any trailing explanation after closing </html> tag
                    end_html = re.search(r"</html>", html_code, re.IGNORECASE)
                    if end_html:
                        html_code = html_code[:end_html.end()]
                    return html_code



            cleaned_code=extract_html_from_llm_response(files)
            print(cleaned_code,flush=True)

            

            with tempfile.TemporaryDirectory() as temp_dir:
                file_path=os.path.join(temp_dir, "index.html")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w",encoding="utf-8") as f:
                    f.write(cleaned_code)





            


               # Write attachment text files (str → encoded as utf-8)
                # for name, text_content in files_text.items():
                #     filepath = os.path.join(temp_dir, name)
                #     os.makedirs(os.path.dirname(filepath), exist_ok=True)
                #     with open(filepath, "w", encoding="utf-8") as f:
                #         f.write(text_content)

                # Write attachment binary files (bytes)
                # print("Writing the image file")
                # if files_binary:
                #     for name, binary_content in files_binary.items():
                #         filepath = os.path.join(temp_dir, name)
                #         os.makedirs(os.path.dirname(filepath), exist_ok=True)
                #         with open(filepath, "wb") as f:
                #             f.write(binary_content)

                print("Writing attachments to temp dir")
                if req.attachments:
                    for file_dict in req.attachments:
                        name = file_dict["name"]
                        _, base64_data = file_dict["url"].split(",", 1)
                        binary_content = base64.b64decode(base64_data)

                        # Save to temp_dir
                        filepath = os.path.join(temp_dir, name)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, "wb") as f:
                            f.write(binary_content)


                with open(os.path.join(temp_dir, "brief.txt"), "w") as f:
                    f.write(req.brief)
                    


                print("Generating readme")
                readme=generate_readme(brief=req.brief,round=req.round,task=req.task)
                print("Writing the README.md for the generated app")
                with open(os.path.join(temp_dir, "README.md"), "w") as f:
                    f.write(readme)

                license_text=generate_mit_license(author_name=req.email.split('@')[0])
                print("Writing the license")
                with open(os.path.join(temp_dir, "LICENSE"), "w") as f:
                    f.write(license_text)

                print("Creating the repo")
                repo = create_repo(req.task)
                print("Repo created")
                print("Pushing the generated code to the repo",flush=True)
                commit_sha = push_code(repo["clone_url"], temp_dir)
                print("Successfully pushed the code",flush=True)
                print("Enabling git pages",flush=True)
                enable_github_pages(repo["full_name"])
                print("Successfully enabled git pages",flush=True)

                global repo_store

                # Save repo info for later (keyed by task)
                repo_store= {
                    "repo_url": repo["clone_url"],
                    "pages_url": f"https://{repo['owner']['login']}.github.io/{repo['name']}/",
                    "html_url": repo["html_url"]
                }


                print("Sending evaluation request",flush=True)

                print(req.evaluation_url, {
                    "email": req.email,
                    "task": req.task,
                    "round": req.round,
                    "nonce": req.nonce,
                    "repo_url": repo["html_url"],
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo['owner']['login']}.github.io/{repo['name']}/"
                },flush=True)

                notify_evaluator(req.evaluation_url, {
                    "email": req.email,
                    "task": req.task,
                    "round": req.round,
                    "nonce": req.nonce,
                    "repo_url": repo["html_url"],
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo['owner']['login']}.github.io/{repo['name']}/"
                })
                
        if req.round==2:

            print("Round 2: Starting revision process",flush=True)

            repo_dir = tempfile.mkdtemp()

            if repo_store:

                print("Cloning the existing repo to get current code")
                print(repo_store)
                repo_url =  repo_store["repo_url"]
                html_url = repo_store["html_url"]
                

            else:
                print("Fetching clone url",flush=True)
                owner='23f3001761'
                repo_name=req.task
                url = f"https://api.github.com/repos/{owner}/{repo_name}"
                headers = {}
            
                if GITHUB_TOKEN:
                    headers['Authorization'] = f'token {GITHUB_TOKEN}'
            
                response = requests.get(url, headers=headers)
            
                if response.status_code == 200:
                    data = response.json()
                    repo_url= data['clone_url']  # This is the GitHub repo URL
                    html_url=data['html_url']
                elif response.status_code == 404:
                    return "Repository not found."
                else:
                    return f"Error: {response.status_code} - {response.text}"


            upload_dir = "/tmp"
            file_paths = {}
            if req.attachments:
                image_present=False
                #save the files 
                image_data=[]

                for dict in req.attachments:
                    if dict['url'].startswith("data:image/"):
                        image_present=True
                        image_data.append({'url':dict['url']})
                    filepath = os.path.join(upload_dir, dict['name'])
                    _, base64_data = dict['url'].split(",", 1)
                    decoded_bytes = base64.b64decode(base64_data)
                    with open(filepath, "wb") as f:
                        f.write(decoded_bytes)

                file_paths[dict['name']]=filepath

                print("Saved files",flush=True)


            

            os.system(f"git clone {repo_url} {repo_dir}")

            print("Reading current files from repo",flush=True)
            other_files = []
            html_content = None
            for root, _, files in os.walk(repo_dir):
                if '.git' in root.split(os.sep):
                    continue 
                for file in files:
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, repo_dir)
                    if file == "index.html":
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            html_content = f.read().strip()
                            soup = BeautifulSoup(html_content, "html.parser")

                            # Prettify it (adds indentation and newlines)
                            pretty_html = soup.head.prettify()
                    elif file == "brief.txt":
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            first_brief=f.read().strip()
                        
                    else:
                        if rel_path not in ['LICENSE', 'README.md']:
                            target_path = os.path.join(upload_dir, rel_path)
                            with open(filepath, "rb") as source_file:
                                binary_content = source_file.read()
                            with open(target_path, "wb") as target_file:
                                target_file.write(binary_content)
                            file_paths[rel_path]=target_path
            
            
            
            print("html_content :",pretty_html)
            #print("other_files :",other_files)




            if req.attachments:

                print("Sending brief, attachments and existing code to the LLM",flush=True)
                updated_files = revise_app_code(
                    brief=req.brief,
                    file_paths=file_paths if file_paths else None,
                    html_content=pretty_html,
                    #other_files=other_files,
                    image_present=image_present,
                    image_data=image_data,
                    repo_url=repo_url,
                    first_brief=first_brief
                )

            else:
                print("Sending brief without attachments and existing code to the LLM",flush=True)
                updated_files = revise_app_code(
                    brief=req.brief,
                    file_paths=file_paths if file_paths else None,
                    html_content=pretty_html,
                    #other_files=other_files,
                    image_present=False,
                    image_data=[],
                    repo_url=repo_url,
                    first_brief=first_brief
                )
                


                
            print("LLM returned updated files",flush=True)



            def extract_html_from_llm_response(response: str) -> str:
                """
                Extracts the HTML code inside markdown ```html fences from an LLM response,
                removes any explanation text before or after, and returns clean HTML.
                If no markdown fences found, tries to locate the first <!DOCTYPE and returns from there.
                Args:
                    response (str): Raw LLM response string.
                Returns:
                    str: Cleaned HTML string starting with <!DOCTYPE.
                Raises:
                    ValueError: if no HTML code found.
                """

                response = response.strip()

                # 0. Early return: Check if response is already valid HTML
                if re.match(r"^(<!DOCTYPE|<html)", response, re.IGNORECASE):
                    return response


                # 1. Try to extract content inside ```html ... ```
                fence_pattern = re.compile(r"```html\s*(.*?)```", re.DOTALL | re.IGNORECASE)
                match = fence_pattern.search(response)
                if match:
                    html_code = match.group(1).strip()
                    # Confirm it starts with <!DOCTYPE or <html>
                    if re.match(r"^(<!DOCTYPE|<html)", html_code, re.IGNORECASE):
                        return html_code

                # 2. Fallback: find first <!DOCTYPE in entire response and return from there
                doctype_match = re.search(r"<!DOCTYPE", response, re.IGNORECASE)
                if doctype_match:
                    html_code = response[doctype_match.start():].strip()
                    # Cut off any trailing explanation after closing </html> tag
                    end_html = re.search(r"</html>", html_code, re.IGNORECASE)
                    if end_html:
                        html_code = html_code[:end_html.end()]
                    return html_code
                
                return html_code

            
    
            print("updated_files :",updated_files)

            cleaned_code=extract_html_from_llm_response(updated_files)
            print(cleaned_code)


            # decoded_html = cleaned_code.encode().decode("unicode_escape")
            # soup = BeautifulSoup(decoded_html, "html.parser")
            # pretty_html = soup.prettify()
            # print(pretty_html)





            with tempfile.TemporaryDirectory() as temp_dir:
                file_path=os.path.join(temp_dir, "index.html")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w",encoding="utf-8") as f:
                    f.write(cleaned_code)   #pretty_html




                print("Writing attachments to temp dir")
                if req.attachments:
                    for file_dict in req.attachments:
                        name = file_dict["name"]
                        if name in other_files:
                            continue
                        _, base64_data = file_dict["url"].split(",", 1)
                        binary_content = base64.b64decode(base64_data)

                        # Save to temp_dir
                        filepath = os.path.join(temp_dir, name)
                        with open(filepath, "wb") as f:
                            f.write(binary_content)


            

            # with tempfile.TemporaryDirectory() as temp_dir:
            #     for name, content in updated_files.items():
            #         filepath = os.path.join(temp_dir, name)
            #         os.makedirs(os.path.dirname(filepath), exist_ok=True)
            #         with open(filepath, "wb") as f:
            #             f.write(content)

                print("Updating README.md",flush=True)
                readme=generate_readme(brief=req.brief,round=req.round,task=req.task)
                readme_path = os.path.join(temp_dir, "README.md")
                if "README.md" not in updated_files:
                    with open(readme_path, "w") as f:
                        f.write(readme)



                print("Preparing to push updated code")
                commit_sha = push_code(repo_url, temp_dir)

                print("Sending evaluation update")
                print(req.evaluation_url, {
                    "email": req.email,
                    "task": req.task,
                    "round": req.round,
                    "nonce": req.nonce,
                    "repo_url": html_url,
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo_url.split('/')[-2]}.github.io/{repo_url.split('/')[-1].replace('.git','')}/"
                },flush=True)
                notify_evaluator(req.evaluation_url, {
                    "email": req.email,
                    "task": req.task,
                    "round": req.round,
                    "nonce": req.nonce,
                    "repo_url": html_url,
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo_url.split('/')[-2]}.github.io/{repo_url.split('/')[-1].replace('.git','')}/"
                })

                if os.path.exists(repo_dir):
                    shutil.rmtree(repo_dir, ignore_errors=True)
    
    except Exception as e:
        # TODO: You may want to log this or notify a failure endpoint
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno
        print(f"[ERROR] Failed processing task {req.task}: {e} : {line_number}")