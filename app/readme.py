def generate_readme(brief='To generate an app with certain specifications',round=1):
    if round ==1:
        return f"""# Auto App Generator

## Summary

This FastAPI-based service receives a request with a **brief** describing an app to build. It uses an **LLM** to generate code, deploys the app to **GitHub Pages**, and notifies an evaluation API. Each request can result in a unique app.

**Example Brief:**  
_{brief}_

## Setup

1. **Clone & enter directory**  
```bash  
git clone https://github.com/your-username/your-repo.git  
cd your-repo  
```  

2. **Install dependencies**  
```bash
python -m venv venv && source venv/bin/activate  
pip install -r requirements.txt  
```  

3. **Create .env**  
    It should contain the following variables:  
    - SERVER_SECRET=your_secret  
    - OPENAI_API_KEY=your_openai_key  
    - GITHUB_TOKEN=your_github_token  

4. **Run**  
    uvicorn main:app --reload  

## Usage

Send a POST to /api-endpoint with a JSON body like:  


The app validates the secret, uses LLM to build the app, pushes it to GitHub Pages, and pings the evaluation API.

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

MIT License © 2025 23f3001761
"""

    else:
        return f"""# Auto App Generator - Revised Version 2

## Summary

This FastAPI-based service receives a request with a **brief** describing an app to build. It uses an **LLM** to generate code, deploys the app to **GitHub Pages**, and notifies an evaluation API. Each request can result in a unique app.

**Example Brief:**  
_{brief}_

## Revised Version  

A second request was made to the api to modify this app to include the changes given in the brief above.  

## Setup

1. **Clone & enter directory**  
```bash  
git clone https://github.com/your-username/your-repo.git  
cd your-repo  
```  

2. **Install dependencies**  
```bash
python -m venv venv && source venv/bin/activate  
pip install -r requirements.txt  
```  

3. **Create .env**  
    It should contain the following variables:  
    - SERVER_SECRET=your_secret  
    - OPENAI_API_KEY=your_openai_key  
    - GITHUB_TOKEN=your_github_token  

4. **Run**  
    uvicorn main:app --reload  

## Usage

Send a POST to /api-endpoint with a JSON body like

The app validates the secret, uses LLM to build the app, pushes it to GitHub Pages, and pings the evaluation API.

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

MIT License © 2025 23f3001761
"""

