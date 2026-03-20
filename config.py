import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY     = os.getenv("SECRET_KEY", "change-me")
    GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    MYSQL_HOST     = os.getenv("MYSQL_HOST",     "ballast.proxy.rlwy.net")
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 31131))
    MYSQL_USER     = os.getenv("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "VOSsgLQblYisXhRlqemFaEpFfGMDFukx")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "railway")
    MAX_ROWS       = int(os.getenv("MAX_ROWS",   500))
