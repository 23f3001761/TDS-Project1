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
    checks: list
    attachments: list = []

SERVER_SECRET=os.getenv("SERVER_SECRET")

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
    try:
        if req.round == 1:
            print("Started the llm request")
            if req.attachments:
                print("Sending brief with attachments")
                files = generate_app_code(req.brief,req.attachments)
                print("Received the response from the llm")
                # print(req.attachments)
                files_text, summary, files_binary = process_attachments(req.attachments)
            else:
                print("Sending brief without attachments")
                files=generate_app_code(req.brief,None)
                print("Received the response from the llm")
                files_txt,summary,files_binary=None,None,None

            print("Starting the temp directory")
            with tempfile.TemporaryDirectory() as temp_dir:
                for name, content in files.items():
                    filepath = os.path.join(temp_dir, name)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(content)



               # Write attachment text files (str → encoded as utf-8)
                # for name, text_content in files_text.items():
                #     filepath = os.path.join(temp_dir, name)
                #     os.makedirs(os.path.dirname(filepath), exist_ok=True)
                #     with open(filepath, "w", encoding="utf-8") as f:
                #         f.write(text_content)

                # Write attachment binary files (bytes)
                print("Writing the image file")
                if files_binary:
                    for name, binary_content in files_binary.items():
                        filepath = os.path.join(temp_dir, name)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, "wb") as f:
                            f.write(binary_content)

                print("Generating readme")
                readme=generate_readme(brief=req.brief,round=req.round)
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
                print("Pushing the generated code to the repo")
                commit_sha = push_code(repo["clone_url"], temp_dir)
                print("Successfully pushed the code")
                print("Enabling git pages")
                enable_github_pages(repo["full_name"])
                print("Successfully enabled git pages")

                global repo_store

                # Save repo info for later (keyed by task)
                repo_store= {
                    "repo_url": repo["clone_url"],
                    "pages_url": f"https://{repo['owner']['login']}.github.io/{repo['name']}/",
                    "html_url": repo["html_url"]
                }


                print("Sending evaluation request")

                print(req.evaluation_url, {
                    "email": req.email,
                    "task": req.task,
                    "round": req.round,
                    "nonce": req.nonce,
                    "repo_url": repo["html_url"],
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo['owner']['login']}.github.io/{repo['name']}/"
                })

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
            print("Round 2: Starting revision process")

            print("Cloning the existing repo to get current code")
            repo_dir = tempfile.mkdtemp()
            print(repo_store)
            repo_url =  repo_store["repo_url"]
            os.system(f"git clone {repo_url} {repo_dir}")

            print("Reading current files from repo")
            existing_files = {}
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    if file.endswith((".html", ".js", ".css", ".py", ".md")):
                        filepath = os.path.join(root, file)
                        rel_path = os.path.relpath(filepath, repo_dir)
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            existing_files[rel_path] = f.read()

            print("Sending brief, attachments and existing code to the LLM")
            updated_files = revise_app_code(
                brief=req.brief,
                attachments=req.attachments,
                existing_files=existing_files
            )
            print("LLM returned updated files")

            with tempfile.TemporaryDirectory() as temp_dir:
                for name, content in updated_files.items():
                    filepath = os.path.join(temp_dir, name)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(content)

                print("Updating README.md")
                readme=generate_readme(brief=req.brief,round=req.round)
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
                    "repo_url": repo_url,
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo_url.split('/')[-2]}.github.io/{repo_url.split('/')[-1].replace('.git','')}/"
                })
                notify_evaluator(req.evaluation_url, {
                    "email": req.email,
                    "task": req.task,
                    "round": req.round,
                    "nonce": req.nonce,
                    "repo_url": repo_url,
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{repo_url.split('/')[-2]}.github.io/{repo_url.split('/')[-1].replace('.git','')}/"
                })
    
    except Exception as e:
        # TODO: You may want to log this or notify a failure endpoint
        print(f"[ERROR] Failed processing task {req.task}: {e}")
