import speech_recognition as sr
import subprocess
import time
import json
import difflib

# --- Fuzzy match helper ---
def similar(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening for command... (say 'rambo blink')")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)  # better noise adaptation
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
        except sr.WaitTimeoutError:
            print("⌛ No speech detected. Try again.")
            return ""

        try:
            command = recognizer.recognize_google(audio).lower().strip()
            print(f"[DEBUG] Heard: '{command}'")
            return command
        except sr.UnknownValueError:
            print("😶 I didn't catch that. Speak clearly.")
        except sr.RequestError:
            print("⚠️ Speech API unavailable. Check internet connection.")
        return ""

def main():
    while True:
        command = listen_for_command()

        # --- Fuzzy check for "rambo" and "blink" ---
        words = command.split()
        if any(similar(word, "rambo") > 0.7 for word in words) and \
           any(similar(word, "blink") > 0.7 for word in words):
            print("✅ Command recognized. Starting blink detector...")
            subprocess.call(["python", "eye.py"])
            time.sleep(3)  # wait before listening again

        elif "is the webcam on" in command or "webcam still on" in command:
            try:
                with open("webcam_status.json", "r") as f:
                    status = json.load(f).get("status", "off")
                print(f"📷 Webcam is currently {status}.")
            except FileNotFoundError:
                print("📷 No webcam status file found.")

        elif "exit" in command:
            print("👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
