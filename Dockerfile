FROM python:3.11-slim-buster

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev && \
    apt-get -y update; apt-get -y install curl


COPY . .

EXPOSE 4000

CMD ["python", "main.py"]
