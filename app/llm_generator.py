import openai
import csv
import io
import os
from dotenv import load_dotenv
from file_handling import process_attachments

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_app_code(brief, attachments):

    use_mock=True
    if use_mock:
        print("Sending the mock llm response")
        html=f"<html><body><h1>Mock App for : {brief} </h1><img src='sample.png'ī /></body></html>"
        return {
            "index.html":html.encode('utf-8')
        }

    if attachments!=None and attachments!=[]:
        print("Starting to process attachments")
        files_text, summary, files_binary = process_attachments(attachments)
        print("Received processed attachments")

        print("Creating attachment_info")
        # Build attachment info snippet for the prompt
        attachment_info_lines = []
        # Include text files with first 10 lines or 500 chars snippet
        for fname, content in files_text.items():

            if fname.lower().endswith(".csv"):
                try:
                    reader = csv.reader(io.StringIO(content))
                    headers = next(reader, [])
                    snippet_lines = content.splitlines()[:10]
                    snippet = "\n".join(snippet_lines)
                    if len(snippet) > 500:
                        snippet = snippet[:500] + "..."
                    attachment_info_lines.append(
                        f"CSV file '{fname}':\n- Columns: {headers}\n{snippet}"
                    )
                except Exception as e:
                    attachment_info_lines.append(
                        f"CSV file '{fname}': could not read schema ({str(e)})"
                    )

            else:


                snippet = "\n".join(content.splitlines()[:10])
                if len(snippet) > 500:
                    snippet = snippet[:500] + "..."
                attachment_info_lines.append(f"Text file '{fname}':\n{snippet}")
        # Include summary lines for binary (images) and skipped files from summary
        # The summary string already has info for images and skipped binaries
        if summary:
            attachment_info_lines.append("\nBinary/Other files info:\n" + summary)

        attachment_info = "\n\n".join(attachment_info_lines) if attachment_info_lines else "None"
    else:
        attachment_info="None"
    
    print("Finished creating attachment_info")
    print("attachment_info:", attachment_info)




    # attachment_info = "\n".join([
    #     f"- {a['name']} (data URI provided)" for a in attachments
    # ]) if attachments else "None"


    prompt = f"""Build a minimal web app for this brief: {brief} 
    Attachments (may be needed in the app logic or UI):{attachment_info} 
    Return ONLY the complete content of a single file named 'index.html' as plain text with no explanations. Do NOT return any JSON or additional files."""

    print("Final prompt:",prompt)

    try:
        #clean llm response
        def clean_llm_response(resp_text: str) -> str:
        # Remove markdown code fences if present
            if resp_text.startswith("```"):
                # remove first line and last line if triple backticks
                lines = resp_text.splitlines()
                if lines[-1].strip() == "```":
                    lines = lines[1:-1]
                else:
                    lines = lines[1:]
                return "\n".join(lines).strip()
            return resp_text.strip()

        MINIMAL_HTML="""<!DOCTYPE html>
        <html><head><title>Fallback App</title></head><body><h1>Failed to generate app</h1></body></html>"""


        print("Sending the llm prompt")

        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        raw_code = resp.choices[0].message.content
        print("Received llm response")

        print("Sending llm response for cleaning")
        code=clean_llm_response(raw_code)
        print("Recieved Cleaned llm response")

        print("Validating html in the llm response")
        if "<html" not in code.lower():
            print("Warning: LLM did not return valid HTML, using fallback")
            code = MINIMAL_HTML

        return {"index.html": code.encode("utf-8")}
    except:
        print("OpenAI error")
        code = MINIMAL_HTML
        return {"index.html": code.encode("utf-8")}


def revise_app_code(brief, attachments, existing_files):
    use_mock=True
    if use_mock:
        print("Sending the mock llm response")
        html=f"<html><body><h1>Mock App for : {brief} </h1><h3>Modified second round of requests</h3></body></html>"
        return {
            "index.html":html.encode('utf-8')
        }


    files_text, summary, files_binary = process_attachments(attachments)

    # Build attachment info snippet for the prompt
    attachment_info_lines = []
    # Include text files with first 10 lines or 500 chars snippet
    for fname, content in files_text.items():
        snippet = "\n".join(content.splitlines()[:10])
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        attachment_info_lines.append(f"Text file '{fname}':\n{snippet}")
    # Include summary lines for binary (images) and skipped files from summary
    # The summary string already has info for images and skipped binaries
    if summary:
        attachment_info_lines.append("\nBinary/Other files info:\n" + summary)

    attachment_info = "\n\n".join(attachment_info_lines) if attachment_info_lines else "None"



    #attachment_info = decode_attachments(attachments)

    context = "\n".join([f"--- {name} ---\n{content}" for name, content in existing_files.items()])

    prompt = f"""
    You are given a web application project with the following files:

    {context}

    Your task is to revise this project based on the following new brief:
    "{brief}"

    Make improvements or feature additions accordingly.

    Attachments:
    {attachment_info}

    Return only a single file."""

    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    updated_code = resp.choices[0].message.content
    return {"index.html": updated_code.encode("utf-8")}
    

# Absolutely — you're thinking about this the right way.

# Since the **file types aren't known ahead of time**, you need a general-purpose handler that:

# * Dynamically detects common file types from attachments
# * Decodes the base64 content (if appropriate)
# * Injects the relevant parts into the **LLM prompt**, in a usable and safe format

# ---

# ## ✅ Goal: Generic attachment handler

# This should:

# 1. Detect the file type (`.md`, `.csv`, `.txt`, maybe `.json`)
# 2. Decode the data URI to get the actual content
# 3. Return a string block you can embed into a prompt
# 4. Skip or describe files that aren’t readable (e.g., `.png`, `.zip`)

# ---

# ## ✅ Example: Generalized Attachment Decoder for LLM Prompts

# ````python
# import base64
# import re

# def decode_attachments_for_prompt(attachments, max_chars=1000):
#     result = []
#     for att in attachments:
#         name = att.get("name", "unknown")
#         url = att.get("url", "")
        
#         # Match base64-encoded data URIs
#         match = re.match(r"data:.*?;base64,(.*)", url)
#         if not match:
#             result.append(f"- {name}: Unsupported or missing data URI")
#             continue

#         try:
#             content = base64.b64decode(match.group(1)).decode("utf-8", errors="ignore")
#         except Exception:
#             result.append(f"- {name}: Could not decode")
#             continue

#         # Clean up very long files for prompt safety
#         if len(content) > max_chars:
#             content = content[:max_chars] + "\n... (truncated)"

#         # Determine how to format based on file extension
#         ext = name.split('.')[-1].lower()
#         if ext in ["md", "txt", "csv", "json", "py", "html"]:
#             block = f"File: {name}\n```\n{content}\n```"
#         else:
#             block = f"File: {name}\n(Unsupported or non-text file — not included in prompt)"

#         result.append(block)

#     return "\n\n".join(result)
# ````

# ---

# ### 🧠 Example usage in LLM prompt:

# ```python
# file_snippets = decode_attachments_for_prompt(req.attachments)

# prompt = f"""
# You are to build a web application based on the following brief:

# {req.brief}

# Here are the input files provided as attachments:
# {file_snippets}

# Use these files as needed to complete the task.

# Return a single file: `index.html`
# """
# ```

# ---

# ## ✅ Benefits of this approach

# | Feature                             | Handled?      |
# | ----------------------------------- | ------------- |
# | Dynamically detects text file types | ✅             |
# | Skips or warns about binary files   | ✅             |
# | Prevents huge prompt bloat          | ✅ (truncates) |
# | Reusable across many tasks          | ✅             |
# | Works for Markdown, CSV, JSON, etc  | ✅             |

# ---

# ## 🛑 What this won’t do

# * It won’t **"understand" binary data** (like images or ZIPs) — but it **can** still mention them for awareness
# * It doesn’t automatically wire files into the web app — the LLM needs to do that using the content you provide

# ---

# ## ✅ File types that are safe to pass directly to GPT

# | Extension              | Can be safely passed to LLM? | Notes                               |
# | ---------------------- | ---------------------------- | ----------------------------------- |
# | `.md`                  | ✅ Yes                        | Markdown                            |
# | `.csv`                 | ✅ Yes                        | Especially small tables             |
# | `.json`                | ✅ Yes                        | Structured data                     |
# | `.txt`                 | ✅ Yes                        | Plain text                          |
# | `.py`                  | ✅ Yes                        | Code generation                     |
# | `.html`                | ✅ Yes                        | Readable structure                  |
# | `.png`, `.jpg`, `.zip` | ❌ No                         | Just describe, don't include base64 |

# ---

# ## ✅ Summary

# Yes, you **can and should** build a generalized file processor to:

# * Extract and safely summarize files
# * Dynamically include their content in LLM prompts
# * Allow your app to work for various file types, **even if unknown upfront**

# Let me know if you want a version that also creates summaries/descriptions of unknown files, or stores the files for later use (like for displaying or serving in GitHub Pages).
