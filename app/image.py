# #Here’s the code you should include in your main.py (or a utils file):
# import base64
# import os

# def process_attachments(attachments, save_dir="generated_files"):
#     os.makedirs(save_dir, exist_ok=True)
#     files = {}

#     for attachment in attachments:
#         name = attachment.get("name")
#         url = attachment.get("url")

#         if not name or not url:
#             continue  # skip invalid attachments

#         if url.startswith("data:"):
#             try:
#                 header, encoded = url.split(",", 1)
#                 binary_data = base64.b64decode(encoded)
#                 filepath = os.path.join(save_dir, name)

#                 with open(filepath, "wb") as f:
#                     f.write(binary_data)

#                 files[name] = filepath
#             except Exception as e:
#                 print(f"Failed to process attachment {name}: {e}")
#                 continue

#     return files  # dict of {filename: full path}

# #In process_request() inside main.py:
# def process_request(req: AppRequest):
#     print("Processing request...")

#     # Step 1: Handle attachments (images)
#     attachment_files = process_attachments(req.attachments)

#     # Step 2: Use this image as part of the LLM prompt
#     prompt = build_prompt(req.brief, attachment_files)

#     # Step 3: Call your LLM generator (e.g., OpenAI, GPT4All, Ollama)
#     files = generate_minimal_app(prompt)

#     # Step 4: Create GitHub repo and push
#     repo_url, commit_sha, pages_url = push_to_github_repo(req, files)

#     # Step 5: Notify the evaluation server
#     notify_evaluator(
#         email=req.email,
#         task=req.task,
#         round=req.round,
#         nonce=req.nonce,
#         repo_url=repo_url,
#         commit_sha=commit_sha,
#         pages_url=pages_url,
#         evaluation_url=req.evaluation_url
#     )

# # Modify the LLM prompt builder

# #Create a build_prompt() function like this:

# def build_prompt(brief: str, attachments: dict) -> str:
#     prompt = f"""You are a code generator. Build a minimal web app in a single HTML file that satisfies the following brief:

# {brief}

# """

#     # Include image attachment info if present
#     if attachments:
#         for name, path in attachments.items():
#             prompt += f"\nThe file '{name}' is an image (likely a captcha). Use it in the app as needed. Assume it will be hosted at './{name}' in the same folder as the index.html.\n"

#     prompt += "\nOnly return a complete HTML document (index.html) as output. Do not include explanations or markdown. Just plain HTML."

#     return prompt

# #Use the prompt when calling the LLM

# #In process_request():
# attachment_files = process_attachments(req.attachments)
# prompt = build_prompt(req.brief, attachment_files)

# files = generate_minimal_app(prompt)

# # Add the images into the files dict before pushing to GitHub
# for name, path in attachment_files.items():
#     with open(path, "rb") as f:
#         files[name] = f.read()

