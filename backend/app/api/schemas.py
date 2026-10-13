from pydantic import BaseModel


class GenerateResponse(BaseModel):
    finished: bool = False
    blog: str | None = None
    blog_title: str | None = None
    error: str | None = None