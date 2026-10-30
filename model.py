from pydantic import BaseModel, Field


class Component(BaseModel):
    name: str
    purpose: str
    input: list[str] = Field(default_factory=list)
    output: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class Milestone(BaseModel):
    name: str
    goal: str


class ProjectPlan(BaseModel):
    project_name: str
    problem_statement: str
    target: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    technology: list[str] = Field(default_factory=list)
    component: list[Component] = Field(default_factory=list)
    risk: list[str] = Field(default_factory=list)
    milestone: list[Milestone] = Field(default_factory=list)


# Keep compatibility with existing Agent.py imports
projectplan = ProjectPlan
