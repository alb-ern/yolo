import threading
import time
from main import run_detection

latest = None


def detection_thread():
    global latest
    for direction, _ in run_detection():
        latest = direction


threading.Thread(target=detection_thread, daemon=True).start()

while True:
    print(f"Dir: {latest}")
    time.sleep(0.1)
