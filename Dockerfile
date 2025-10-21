FROM python:3.10-slim

WORKDIR /app

#system dependencies
RUN apt-get update && apt-get install -y \
    git \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /code

#Copy all the code
COPY . .


#dependencies
RUN pip install --no-cache-dir -r requirements.txt 



#HuggingFace port
EXPOSE 7860

#Run FastAPI
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","7860"]