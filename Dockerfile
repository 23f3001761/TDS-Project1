FROM python:3.10-slim

WORKDIR /app

#dependencies
COPY requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 

#app code
COPY app/ ./app/

#HuggingFace port
EXPOSE 7860

#Run FastAPI
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","7860"]
