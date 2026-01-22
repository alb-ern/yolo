# YOLO Head Direction Detection

Real-time head direction detection using YOLO pose estimation. Includes a simple endless runner game controlled by head movement.

## Features

- Head direction detection (-1 to 1 scale: left to right)
- Works with tilted heads using geometric projection
- GPU acceleration (CUDA) when available
- Simple 3D endless runner game demo

## Installation

```bash
pip install ultralytics opencv-python pygame-ce
```

## Usage

### As a module

```python
from yolo import run_detection

for direction, bbox in run_detection():
    print(f"Direction: {direction}")  # -1 (left) to 1 (right)
```

### Debug mode (with GUI)

```bash
python yolo.py
```

### Game demo

```bash
python game.py
```

Control the game by looking left/right to dodge obstacles.

## Files

- `yolo.py` - Head direction detection module
- `game.py` - Endless runner game demo
- `entity.png` - Game obstacle sprite

## Configuration

Edit `game.py` CONFIG section to adjust:

- `LANE_WIDTH` - Distance between lanes
- `MOVE_SPEED` - Obstacle approach speed
- `STEER_SPEED` - Head movement sensitivity

## License

MIT
