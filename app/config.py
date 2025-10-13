import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN=os.getenv("GITHUB_TOKEN")
BASE_GITHUB_ORG=os.getenv('GITHUB_ORG')
SERVER_SECRET=os.getenv("SERVER_SECRET")
GITHUB_API="https://api.github.com"
