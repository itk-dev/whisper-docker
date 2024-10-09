# pull pyhton
FROM python:3.10-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Update PIP
RUN apt update && \
    pip install --no-cache-dir --upgrade pip

WORKDIR /app

# Install dependencies
COPY requirements.txt .
#RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Copy project files
COPY index.py /app/index.py

# Run uvicorn when the container launches
CMD ["python", "-O", "-m", "uvicorn", "index:app", "--host", "0.0.0.0"]