import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class CommandRequest(BaseModel):
    text: str

class LLMCommand(BaseModel):
    mode: int = Field(default=1)
    x_velocity: float = Field(default=0.0, ge=-0.5, le=0.5)
    y_velocity: float = Field(default=0.0, ge=-0.4, le=0.4)
    yaw_velocity: float = Field(default=0.0, ge=-0.8, le=0.8)
    speed: str = Field(default="slow")