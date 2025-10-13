import subprocess
import os
import requests
from config import GITHUB_TOKEN, GITHUB_API
import tempfile

def run_shell(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Shell failed: {cmd}\\n{result.stderr}")
    return result.stdout.strip()


def create_repo(repo_name, private=False):
    print("Starting the repo creation process")
    url = f"{GITHUB_API}/user/repos"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {"name": repo_name, "private": private }
    r = requests.post(url, headers=headers, json=data)
    print("Sent request to git for repo creation")
    r.raise_for_status()
    return r.json()

def enable_github_pages(repo_full_name):
    print("Starting git pages enabling")
    url = f"{GITHUB_API}/repos/{repo_full_name}/pages"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.switcheroo-preview+json"
    }
    data = {"source": {"branch": "main", "path": "/"}}
    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()
    return r.json()

def push_code(clone_url, local_dir):
    print("Starting the code push")

    with tempfile.TemporaryDirectory() as temp_dir:
        clone_path = os.path.join(temp_dir, "repo")

        # Clone into unique subdirectory
        run_shell(f"git clone {clone_url} {clone_path}")

        # Copy generated code into clone directory
        run_shell(f"cp -r {local_dir}/* {clone_path}/")

        # Git config, add, commit, push
        run_shell("git config user.name 'bot'", cwd=clone_path)
        run_shell("git config user.email 'bot@example.com'", cwd=clone_path)
        run_shell("git add .", cwd=clone_path)
        run_shell("git commit -m 'init'", cwd=clone_path)
        run_shell("git push", cwd=clone_path)

    return run_shell("git rev-parse HEAD", cwd="repo_temp")