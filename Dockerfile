# STEP 1: Use Playwright as the base
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

WORKDIR /app

# Install Backend Tools
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

# Install Node.js (To run the Slick UI)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs

# Copy everything
COPY . .

# Build the Frontend (If you put the frontend_page.tsx in a folder named 'app')
# For now, we will run the Backend and it will serve the UI
EXPOSE 8000

CMD ["uvicorn", "backend_main:app", "--host", "0.0.0.0", "--port", "8000"]
