FROM python:3.11-slim-buster
WORKDIR /app
COPY . .
RUN pip install pyproject.toml
CMD ["python", "src/main.py"]