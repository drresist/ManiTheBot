FROM python:3.11-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install pyproject.toml
COPY . .
CMD ["python", "src/main.py"]