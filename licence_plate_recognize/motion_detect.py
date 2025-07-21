import cv2
import numpy as np
import time

CAMERA_INDEX = 0
DIFF_THRESHOLD = 10000000
STILL_FRAMES_REQUIRED = 10
STILL_SCENE_DIFFERENCE = 10000000
CHECK_INTERVAL = 0.2

def compute_diff_score(f1, f2):
    gray1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    return np.sum(thresh)

def wait_for_scene_change(cam):
    print("📷 Waiting for significant change in still scene...")
    _, prev_frame = cam.read()
    prev_still_frame = prev_frame.copy()
    still_count = 0

    while True:
        time.sleep(CHECK_INTERVAL)
        ret, frame = cam.read()
        if not ret:
            continue

        motion_score = compute_diff_score(prev_frame, frame)
        prev_frame = frame

        if motion_score > DIFF_THRESHOLD:
            still_count = 0
            print(f"Motion detected (score={motion_score:.0f})")
        else:
            still_count += 1
            print(f"Still frame {still_count}/{STILL_FRAMES_REQUIRED} (motion={motion_score:.0f})")

        if still_count >= STILL_FRAMES_REQUIRED:
            still_score = compute_diff_score(prev_still_frame, frame)
            print(f"Comparing still scene change: {still_score:.0f}")

            if still_score > STILL_SCENE_DIFFERENCE:
                print("🚗 New object parked — triggering recognition.")
                prev_still_frame = frame.copy()
                return frame

            else:
                print("Scene is still, but not different enough — ignoring.")
                still_count = 0  # reset wait for next change

if __name__ == "__main__":
    cap = cv2.VideoCapture(CAMERA_INDEX)
    try:
        while True:
            trigger_frame = wait_for_scene_change(cap)
            timestamp = int(time.time())
            filename = f"trigger_{timestamp}.jpg"
            cv2.imwrite(filename, trigger_frame)
            print(f"🖼️ Frame saved: {filename}")
            time.sleep(5)
    finally:
        cap.release()
