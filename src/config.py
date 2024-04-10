import os

from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()
        self.TG_MANI_BOT = os.getenv("TG_MANI_BOT")
        self.PG_HOST = os.getenv("PG_HOST")
        self.PG_DB = os.getenv("PG_DB")
        self.PG_USER = os.getenv("PG_USER")
        self.PG_PASS = os.getenv("PG_PASS")
