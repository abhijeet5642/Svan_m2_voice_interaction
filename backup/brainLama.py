import time
import json
import threading
# from groq import AsyncGroq
# from config import GROQ_API_KEY, LLMCommand
from openai import AsyncOpenAI
from config import LLMCommand
from dds_publisher import robot_publisher
from rules import system_rules

# Global State Memory
current_robot_state = {
    "mode": 0,
    "mode_name": "sleep",
    "x_velocity": 0.0,
    "y_velocity": 0.0,
    "yaw_velocity": 0.0,
    "speed": "slow",  
}
command_memory = []

# --- NEW HEARTBEAT FUNCTION ---
def continuous_publish_loop():
    while True:
        # Constantly publish the current state at ~50Hz (every 0.02 seconds)
        robot_publisher.publish_movement(current_robot_state)
        time.sleep(0.02)

# Start the thread immediately
heartbeat_thread = threading.Thread(target=continuous_publish_loop, daemon=True)
heartbeat_thread.start()
# ----------------------------

async def process_text_command(text_command: str):
    global current_robot_state, command_memory
    
    client = AsyncOpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama'
    )
                                                                         
    history_text = "None"
    if command_memory:
        history_text = "\n".join([f"- User: '{cmd['text']}' -> Robot: {cmd['state']}" for cmd in command_memory])

    # Strip out the descriptive 'mode_name' so it doesn't confuse the 1B model
    safe_state_to_show = {
        "mode": current_robot_state["mode"],
        "x_velocity": current_robot_state["x_velocity"],
        "y_velocity": current_robot_state["y_velocity"],
        "yaw_velocity": current_robot_state["yaw_velocity"],
        "speed": current_robot_state["speed"]
    }

    user_prompt = f"""
    CURRENT_STATE: {json.dumps(safe_state_to_show)}
    User: "{text_command}"
    """

    try:
        start_time = time.time()

        response = await client.chat.completions.create(
            model="qwen2.5-coder:3b", # <-- Change this from llama-3.3-70b-versatile
            messages=[
                {"role": "system", "content": system_rules},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=500, # Note: max_completion_tokens is max_tokens in OpenAI
            top_p=1,
            stream=True,
            response_format={"type": "json_object"},
            extra_body={"keep_alive": -1}
            # keep_alive=-1

        )

        raw_message = ""
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                raw_message += chunk.choices[0].delta.content

        print(f"LLM Latency: {(time.time() - start_time):.2f} seconds")

        if not raw_message:
            raise ValueError("Empty response from LLM")

        raw_content = raw_message.strip()
        print(f" 🔍 Raw LLM Output: {raw_content}")

        # Parse JSON
        validated_command = LLMCommand(**json.loads(raw_content))
        current_robot_state = validated_command.model_dump()
        print(f" 🤖 New State Activated: {current_robot_state}")

        # Mode labeling
        mode_labels = {0: "sleep", 1: "stand", 4: "move"}
        current_robot_state["mode_name"] = mode_labels.get(
            current_robot_state.get("mode"), "unknown"
        )

        # Memory
        command_memory.append({
            "text": text_command,
            "state": current_robot_state
        })
        if len(command_memory) > 5:
            command_memory.pop(0)

        # DDS Publish
        robot_publisher.publish_movement(current_robot_state)

        return {"status": "success", "data": current_robot_state}

    except Exception as e:
        print(f"❌ Error: {str(e)}")

        safe_state = {
            "mode": 1,
            "x_velocity": 0.0,
            "y_velocity": 0.0,
            "yaw_velocity": 0.0,
            "speed": "slow"
        }

        robot_publisher.publish_movement(safe_state)
        return {"status": "error", "detail": str(e)}