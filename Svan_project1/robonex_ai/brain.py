import time
import json
import threading
from groq import AsyncGroq
from config import GROQ_API_KEY, LLMCommand
from dds_publisher import robot_publisher
from grokrules import system_rules
# from llamarules import system_rules

# Global State Memory
state_lock = threading.Lock()
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
        with state_lock:
            state_to_publish = current_robot_state.copy()
        robot_publisher.publish_movement(state_to_publish)
        time.sleep(0.02)

# Start the thread immediately
heartbeat_thread = threading.Thread(target=continuous_publish_loop, daemon=True)
heartbeat_thread.start()
# ----------------------------

async def process_text_command(text_command: str):
    global current_robot_state, command_memory
    
    client = AsyncGroq(api_key=GROQ_API_KEY)

    

    with state_lock:
        history_text = "None"
        if command_memory:
            history_text = "\n".join([f"- User: '{cmd['text']}' -> Robot: {cmd['state']}" for cmd in command_memory])

        current_state_snapshot = current_robot_state.copy()

    user_prompt = f"""
    PREVIOUS COMMAND HISTORY: {history_text}
    LAST ROBOT STATE: {current_state_snapshot}
    NEW USER COMMAND: '{text_command}'
    """

    try:
        start_time = time.time()

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_rules},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_completion_tokens=500,
            top_p=1,
            # reasoning_effort="medium",
            stream=True,
            stop=None,
            response_format={"type": "json_object"}
        )

        raw_message = ""
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                raw_message += chunk.choices[0].delta.content

        print(f"LLM Latency: {(time.time() - start_time):.2f} seconds")

        if not raw_message:
            raise ValueError("Empty response from LLM")

        raw_content = raw_message.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
        raw_content = raw_content.strip()

        # Parse JSON
        validated_command = LLMCommand(**json.loads(raw_content))

        with state_lock:
            current_robot_state = validated_command.model_dump()

            # Mode labeling
            mode_labels = {0: "sleep", 1: "stand", 4: "move"}
            current_robot_state["mode_name"] = mode_labels.get(
                current_robot_state.get("mode"), "unknown"
            )

            # Memory
            command_memory.append({
                "text": text_command,
                "state": current_robot_state.copy()
            })
            if len(command_memory) > 5:
                command_memory.pop(0)

            state_to_return = current_robot_state.copy()

        print(f" 🤖 New State Activated: {state_to_return}")

        # DDS Publish
        # robot_publisher.publish_movement(state_to_return)

        return {"status": "success", "data": state_to_return}

    except Exception as e:
        print(f"❌ Error: {str(e)}")

        safe_state = {
            "mode": 1,
            "x_velocity": 0.0,
            "y_velocity": 0.0,
            "yaw_velocity": 0.0,
            "speed": "slow"
        }

        # robot_publisher.publish_movement(safe_state)
        return {"status": "error", "detail": str(e)}