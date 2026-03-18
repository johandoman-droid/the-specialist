FROM mcr.microsoft.com/playwright/python:v1.40.0-focal
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
COPY backend_main.py .
EXPOSE 8000
CMD ["uvicorn", "backend_main:app", "--host", "0.0.0.0", "--port", "8000"]
