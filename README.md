# TDS-Project1

This is a FastAPI + Docker-based project that automates the process of generating, deploying, and updating web applications using LLMs. receives a request with a **brief** describing an app to build. It uses an **LLM** to generate code, deploys the app to **GitHub Pages**, and notifies an evaluation API. Each request can result in a unique app.


## Summary  

This project builds web apps in 2 phases:

###  Build Phase (`/round1`)
- Receives an app brief and secret
- Verifies the request
- Uses an LLM to generate app code
- Creates a GitHub Repository with the generated code
- Deploys the app to **GitHub Pages**
- Sends repo metadata (repo URL, commit SHA, pages URL) to an **evaluation API**

###  Revise Phase (`/round2`)
- Verifies a second request with the same secret
- Updates the app based on a new brief
- Re-deploys to GitHub Pages
- Sends updated repo metadata to an **evaluation API**

**Example Brief:**  
```
Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample.
```

## Setup

### 1. Prerequisites

- Python 3.10+
- Docker and Docker Compose
- GitHub account with a Personal Access Token (PAT) for repo creation and deployment
- OpenAI API key (or compatible LLM)

### 2. Clone the repo

```bash
git clone https://github.com/your-org/auto-app-builder.git
cd auto-app-builder
```  

### 3. Create .env

  It should contain the following variables:  
  - SERVER_SECRET=your_secret  
  - OPENAI_API_KEY=your_openai_key  
  - GITHUB_TOKEN=your_github_token  

### 4. Run 
    uvicorn main:app --reload  

## Usage

Send a POST to /api-endpoint with a JSON body like:  

```json
{
  "email": "student@example.com",
  "secret": "abc123",
  "task" : "A",
  "round" : 1,
  "nonce" : "12ade",
  "brief": "Build a static site to show daily sales",
  "attachments":[{}],
  "evaluation_url" : "https://....."  
}
```

The app :  

  - Verifies the payload

  - Calls LLM to generate code (HTML/JS/CSS)

  - Pushes to a GitHub repo

  - Deploys to GitHub Pages

  - Sends metadata to evaluation_url

A similar request is sent for round 2 which will modify the previously generated code and redeploy the app on Github Pages.

## Code Explanation

* main.py: API & control flow  

* config.py: Loads the environment variables

* llm_generator.py: GPT-based app generation  

* github_utils.py: GitHub API interactions  

* file_handling.py: Processes attachments (text, images)  

* evaluator.py: Notifies evaluation API  

* Dockerfile: Docker support for deployment 

* mit_license.py: Contains the template for the MIT License  

* readme.py: Contains the template for the README.md file for the generated github repository  

* Deployed on Hugging Face Spaces  

## License

This project is licensed under the MIT License.

MIT License © 2025 23f3001761



