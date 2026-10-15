from pydantic import BaseModel, Field

from app.graph.state import Task


class OutlineResponse(BaseModel):
    approval_id: str
    topic: str
    blog_title: str
    sections: list[Task]


class OutlineRevisionRequest(BaseModel):
    instructions: str = Field(default="", max_length=2000)
