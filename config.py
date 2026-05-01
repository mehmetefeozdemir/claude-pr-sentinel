import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GITHUB_TOKEN: str = os.environ["GITHUB_TOKEN"]
    GITHUB_WEBHOOK_SECRET: str = os.environ["GITHUB_WEBHOOK_SECRET"]
    ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
    PORT: int = int(os.getenv("PORT", "8000"))
    CLAUDE_MODEL: str = "claude-sonnet-4-6"


config = Config()
