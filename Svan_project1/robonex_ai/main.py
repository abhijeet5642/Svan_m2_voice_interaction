import threading
import uvicorn
from api import app
from microphone import mic_listen_loop

def main():
    print(" Starting Robot Brain (DDS Enabled)...")
    
    # Start the microphone in the background
    mic_thread = threading.Thread(target=mic_listen_loop, daemon=True)
    mic_thread.start()
    
    # Start the FastAPI web server on the main thread
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()