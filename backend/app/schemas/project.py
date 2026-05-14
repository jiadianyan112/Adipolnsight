from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    research_goal: str = ""
    exposure: str = ""
    outcome: str = ""
    mediator_set: str = ""


class ProjectResponse(BaseModel):
    id: int
    name: str
    research_goal: str
    exposure: str
    outcome: str
    mediator_set: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
