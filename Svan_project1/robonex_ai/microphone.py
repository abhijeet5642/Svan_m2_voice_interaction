import time
import asyncio
import speech_recognition as sr
from brain import process_text_command

def mic_listen_loop():
    recognizer = sr.Recognizer()
    
    # 1. Create a permanent asynchronous engine for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with sr.Microphone() as source:
        print("\nAdjusting for background noise (shhh...)")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Microphone is now continuously listening!")
        
        while True:
            try:
                # Listen in short bursts
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                text = recognizer.recognize_google(audio)
                print(f"\n  said to Svan: '{text}'")
                
                # 2. Run the brain using our permanent engine!
                loop.run_until_complete(process_text_command(text))
                
            except sr.WaitTimeoutError:
                continue 
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"Microphone glitch: {e}")
                time.sleep(1)