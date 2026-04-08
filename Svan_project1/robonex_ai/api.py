from fastapi import FastAPI
from config import CommandRequest
from brain import process_text_command

app = FastAPI()

@app.post("/command")
async def receive_command(request: CommandRequest):
    text_command = request.text.strip()
    print(f"\n[WEB] User Said: '{text_command}'")
    return await process_text_command(text_command)