from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    sqs_url: str = ""

    class Config:
        env_file = ".env"
