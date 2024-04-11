FROM python:3.11-slim-buster
WORKDIR /app
COPY pyproject.toml .
RUN pip install pyproject.toml
COPY . .
CMD ["python", "src/main.py"]