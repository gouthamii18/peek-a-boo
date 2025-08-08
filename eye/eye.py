import cv2
import mediapipe as mp
import time
from gtts import gTTS
import pygame
import os
import numpy as np
import subprocess
import json

# === Initialize ===
pygame.mixer.init()
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# === EAR Calculation ===
def calculate_EAR(landmarks, eye_indices, image_w, image_h):
    coords = [(int(landmarks[i].x * image_w), int(landmarks[i].y * image_h)) for i in eye_indices]
    hor = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))
    ver1 = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
    ver2 = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
    EAR = (ver1 + ver2) / (2.0 * hor)
    return EAR

# === Speak ===
def speak(text):
    tts = gTTS(text=text, lang="en")
    tts.save("blinks.mp3")
    pygame.mixer.music.load("blinks.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue
    os.remove("blinks.mp3")

# === Blink Detection Settings ===
BLINK_THRESH = 0.22
CONSEC_FRAMES = 3
blink_counter = 0
frame_counter = 0

# Track launched apps
launched_apps = set()

# Eye indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# === Open Webcam ===
cap = cv2.VideoCapture(0)

# Mark webcam ON
with open("webcam_status.json", "w") as f:
    json.dump({"status": "on"}, f)

start_time = time.time()
max_duration = 30  # seconds

while True:
    success, frame = cap.read()
    if not success:
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = face_mesh.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            ih, iw, _ = image.shape

            left_EAR = calculate_EAR(face_landmarks.landmark, LEFT_EYE, iw, ih)
            right_EAR = calculate_EAR(face_landmarks.landmark, RIGHT_EYE, iw, ih)
            avg_EAR = (left_EAR + right_EAR) / 2.0

            if avg_EAR < BLINK_THRESH:
                frame_counter += 1
            else:
                if frame_counter >= CONSEC_FRAMES:
                    blink_counter += 1
                    print(f"🫣 Blink detected! Total: {blink_counter}")
                    frame_counter = 0

                    # === App Launch Logic ===
                    if blink_counter == 3 and "notepad" not in launched_apps:
                        print("🚀 Launching Notepad after 3 blinks...")
                        subprocess.Popen(["notepad.exe"])
                        launched_apps.add("notepad")

                    elif blink_counter == 6 and "calculator" not in launched_apps:
                        print("🧮 Launching Calculator after 6 blinks...")
                        subprocess.Popen(["calc.exe"])
                        launched_apps.add("calculator")

                    elif blink_counter == 9 and "spotify" not in launched_apps:
                        print("🎵 Launching Spotify after 9 blinks...")
                        subprocess.Popen(["C:\\Users\\USER\\Downloads\\SpotifySetup.exe"])

                        launched_apps.add("spotify")

    # Show blink count on screen
    cv2.putText(image, f"Blinks: {blink_counter}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Rambo - Blink Detection", image)

    if time.time() - start_time > max_duration:
        break
    if cv2.waitKey(5) & 0xFF == 27:  # ESC to exit early
        break

# === Cleanup ===
cap.release()
cv2.destroyAllWindows()

# Mark webcam OFF
with open("webcam_status.json", "w") as f:
    json.dump({"status": "off"}, f)

# Speak final results
result_text = f"You blinked {blink_counter} time{'s' if blink_counter != 1 else ''} in {max_duration} seconds."
print("🤖 Rambo:", result_text)
speak(result_text)

closing_message = "Blink analysis is complete. Webcam is now closing."
print("📷 Webcam closed.")
speak(closing_message)
