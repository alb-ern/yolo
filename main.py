"""Head direction detection using YOLO pose."""
import cv2
import time
import numpy as np
import torch
from ultralytics import YOLO

_device = "cuda" if torch.cuda.is_available() else "cpu"
_model = YOLO("yolo26m-pose.pt").to(_device)


def get_head_direction(kpts):
    """Returns -1 (right) to 1 (left)."""
    nose, l_eye, r_eye = kpts[:3]
    eye_center = (l_eye[:2] + r_eye[:2]) / 2
    eye_vec = r_eye[:2] - l_eye[:2]
    eye_dist = np.linalg.norm(eye_vec)
    if eye_dist < 1:
        return 0.0
    offset = np.dot(nose[:2] - eye_center, eye_vec / eye_dist) / eye_dist
    return round(np.clip(offset * 12, -1, 1), 2)


def _init_camera(camera_id=0):
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap


def run_detection(camera_id=0, debug=False):
    """Yields (direction, bbox) per person. debug=True shows GUI."""
    cap = _init_camera(camera_id)
    prev = time.time()

    while True:
        frame = cap.read()[1]
        results = _model(frame, verbose=False)[0]
        kpts = results.keypoints.data.cpu().numpy() if results.keypoints else []
        boxes = results.boxes

        for i, k in enumerate(kpts):
            direction = get_head_direction(k)
            bbox = boxes[i].xyxy[0].cpu().numpy() if boxes else None
            yield direction, bbox

            if debug and bbox is not None:
                annotated = results.plot()
                cv2.putText(annotated, f"Dir: {direction}", (int(bbox[0]), int(bbox[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                now = time.time()
                cv2.putText(annotated, f"FPS: {1 / (now - prev):.0f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                prev = now
                cv2.imshow("YOLO", annotated)
                if cv2.waitKey(1) == ord('q'):
                    return


if __name__ == "__main__":
    print(f"Debug | {_device}")
    for d, b in run_detection(debug=True):
        pass
