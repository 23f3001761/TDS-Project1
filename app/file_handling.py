from typing import List, Dict
from pydantic import BaseModel
import base64
import mimetypes

class Attachment(BaseModel):
    name: str
    url: str




def process_attachments(attachments: List[dict]):
    """
    Returns:
    - files_text: filename -> text content (for text files)
    - summary: descriptive string about files for LLM prompt
    - files_binary: filename -> bytes content (for images)
    """
    print("Received attachemnts to process")
    files_text = {}
    files_binary = {}
    summary_lines = []

    for att in attachments:
        name = att['name']
        url = att['url']
        mime, _ = mimetypes.guess_type(name)
        is_text = mime and mime.startswith("text")
        is_image = mime and mime.startswith("image")

        if url.startswith("data:"):
            base64_data = url.split(",", 1)[1]
            try:
                decoded = base64.b64decode(base64_data)
                if is_text:
                    content = decoded.decode("utf-8")
                    files_text[name] = content
                    summary_lines.append(f"- {name}: text file with {len(content.splitlines())} lines")
                elif is_image:
                    files_binary[name] = decoded
                    summary_lines.append(f"- {name}: image file ({mime})")
                else:
                    summary_lines.append(f"- {name}: binary file (type: {mime}), skipped saving")
            except Exception as e:
                summary_lines.append(f"- {name}: unreadable file ({str(e)})")
        else:
            summary_lines.append(f"- {name}: external URL (not base64)")

    print("Sent processed attachements")
    # print('text:',files_text)
    # print('binary:',files_binary)
    print('summary:',"\n".join(summary_lines))

    return files_text, "\n".join(summary_lines), files_binary