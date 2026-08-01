from typing import Literal
from pydantic import BaseModel, Field

class ReviewOptions(BaseModel):
    provider: Literal["mock", "llm"] = "mock"
    maxFindings: int = Field(default=100, ge=1)

# Model request yang diterima daripada client
class ReviewRequest(BaseModel):
    diff: str
    options: ReviewOptions = ReviewOptions()

# Model response yang dipulangkan selepas job berjaya diterima
class ReviewResponse(BaseModel):
    jobId: str
    status: str
