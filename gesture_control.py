"""
gesture_control.py
Prototype: hand gesture recognition + finger counting -> map to desktop commands.

Requirements:
 pip install opencv-python mediapipe pyautogui numpy
"""

import time
import math
import numpy as np
import cv2
import mediapipe as mp
import pyautogui

# ------------------ Configuration ------------------
# Map finger counts to functions (customize)
# 0: mute/play-pause  (example)
# 1: next slide / right arrow
# 2: previous slide / left arrow
# 3: volume up
# 4: volume down
# 5: toggle full-screen (F11)
ACTION_MAP = {
    0: "play_pause",
    1: "next",
    2: "prev",
    3: "vol_up",
    4: "vol_down",
    5: "full_toggle"
}

# cooldown in seconds per gesture to avoid repeat spam
COOLDOWN = 1.0

# which camera index (0 default)
CAM_INDEX = 0

# ---------------------------------------------------

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# store last action time
last_time_action = {k: 0 for k in ACTION_MAP.keys()}

# helper action functions using pyautogui
def do_action(action_name):
    # print the action for debugging
    print(f"Action: {action_name}  [{time.strftime('%H:%M:%S')}]")
    if action_name == "next":
        pyautogui.press('right')
    elif action_name == "prev":
        pyautogui.press('left')
    elif action_name == "vol_up":
        # cross-platform approach: press volume up key if available
        try:
            pyautogui.press('volumeup')
        except Exception:
            # fallback: send ctrl+up or custom mapping
            pyautogui.hotkey('ctrl', 'up')
    elif action_name == "vol_down":
        try:
            pyautogui.press('volumedown')
        except Exception:
            pyautogui.hotkey('ctrl', 'down')
    elif action_name == "play_pause":
        try:
            pyautogui.press('playpause')
        except Exception:
            pyautogui.press('space')
    elif action_name == "full_toggle":
        # F11 typical fullscreen toggle in browsers
        pyautogui.press('f11')

# finger indices in MediaPipe:
# Thumb: tip 4, ip 3, mcp 2, cmc 1
# Index: tip 8, pip 6
# Middle: tip 12, pip 10
# Ring: tip 16, pip 14
# Pinky: tip 20, pip 18

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]  # for thumb we use 3 (ip)

def count_fingers(hand_landmarks, image_width, image_height, handedness_str):
    """
    Return number of extended fingers (0-5).
    handedness_str: 'Left' or 'Right' from MediaPipe classification (string)
    """
    lm = hand_landmarks.landmark
    fingers_up = []

    # Convert normalized landmarks to pixel coords
    coords = [(int(l.x * image_width), int(l.y * image_height)) for l in lm]

    # Thumb: compare x coordinates depending on handedness
    # If right hand: thumb tip x < ip x means extended (since image origin at left)
    # If left hand: thumb tip x > ip x means extended
    thumb_tip_x = coords[4][0]
    thumb_ip_x = coords[3][0]
    if handedness_str == "Right":
        fingers_up.append(1 if thumb_tip_x < thumb_ip_x else 0)
    else:
        fingers_up.append(1 if thumb_tip_x > thumb_ip_x else 0)

    # For other fingers: tip y < pip y means extended (lower y is up on image)
    for tip_idx, pip_idx in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
        tip_y = coords[tip_idx][1]
        pip_y = coords[pip_idx][1]
        fingers_up.append(1 if tip_y < pip_y else 0)

    return sum(fingers_up), fingers_up

def main():
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check camera index or permissions.")
        return

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            # Flip for mirror view
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            result = hands.process(frame_rgb)

            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    # handedness classification: 'Left' or 'Right'
                    hand_label = handedness.classification[0].label

                    finger_count, finger_states = count_fingers(hand_landmarks, w, h, hand_label)

                    # draw landmarks
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # show count on screen
                    cv2.putText(frame, f'Count: {finger_count}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 2)

                    # decide action
                    if finger_count in ACTION_MAP:
                        action = ACTION_MAP[finger_count]
                        now = time.time()
                        if now - last_time_action[finger_count] > COOLDOWN:
                            do_action(action)
                            last_time_action[finger_count] = now

                    # optionally show which fingers are up (for debugging)
                    cv2.putText(frame, f'States: {finger_states}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 1)

            # show frame
            cv2.imshow("Gesture Control", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # Esc to quit
                break
            # (optional) press 'c' to capture screenshot / debug
            if key == ord('c'):
                ts = int(time.time())
                cv2.imwrite(f"screenshot_{ts}.png", frame)
                print("Saved screenshot")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
