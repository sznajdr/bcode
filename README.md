# Snooker Match Tracker

An end-to-end computer vision system for automatic snooker match analysis, combining object detection, multi-object tracking, and rule-based game state inference to generate frame-accurate play-by-play commentary from broadcast video.

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Table Calibration](#table-calibration)
5. [Inference Pipelines](#inference-pipelines)
6. [Cloud Deployment (Google Colab)](#cloud-deployment)
7. [Model Training](#model-training)
8. [Validation Tools](#validation-tools)
9. [Output Specification](#output-specification)
10. [Command Reference](#command-reference)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This system implements a multi-stage pipeline for snooker match analysis:

1. **Detection**: YOLOv8-based ball detection across 8 classes (cue ball, 15 reds, 6 colors)
2. **Tracking**: ByteTrack multi-object tracking with color-aware identity management
3. **Coordinate Mapping**: Perspective transformation from pixel to normalized table coordinates
4. **Shot Segmentation**: Motion-based shot boundary detection with velocity thresholding
5. **Game State Inference**: Rule engine implementing World Snooker Tour regulations
6. **Commentary Generation**: Structured event extraction with natural language output

The system supports multiple inference backends (local GPU, cloud API, local inference server) and includes optimizations for processing long-form broadcast content.

---

## System Requirements

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | ≥3.8 | Runtime |
| opencv-python | ≥4.5 | Video I/O, image processing |
| numpy | ≥1.20 | Numerical operations |
| matplotlib | ≥3.5 | Visualization |

### Local Inference

| Package | Version | Purpose |
|---------|---------|---------|
| ultralytics | ≥8.0 | YOLOv8 implementation |
| torch | ≥2.0 | Deep learning backend |
| supervision | ≥0.16 | ByteTrack integration |

### Roboflow Integration

| Package | Version | Purpose |
|---------|---------|---------|
| inference | ≥0.9 | Local inference server (requires Python <3.13) |

### Training

| Package | Version | Purpose |
|---------|---------|---------|
| ultralytics | ≥8.0 | Training framework |
| pyyaml | ≥6.0 | Configuration parsing |

---

## Installation

```bash
# Full installation (local inference + training)
pip install ultralytics opencv-python numpy matplotlib supervision tqdm pyyaml

# Minimal installation (Roboflow API only)
pip install opencv-python numpy matplotlib

# With local inference server support
pip install inference opencv-python numpy matplotlib supervision
```

Verify installation:
```bash
python -c "import cv2, numpy, matplotlib; print('Core dependencies installed')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## Table Calibration

Calibration establishes the homography matrix for perspective correction, mapping pixel coordinates to normalized table coordinates (0.0–1.0).

### Procedure

```bash
python run_local.py --calibrate --video <input.mp4> [--start-frame <n>]
python run_roboflow.py --calibrate --video <input.mp4> [--start-frame <n>]
```

### Controls

| Input | Action |
|-------|--------|
| Left click | Place corner point |
| ←/→ | Navigate ±1 frame |
| ↑/↓ | Navigate ±10 frames |
| PgUp/PgDn | Navigate ±100 frames |
| Home/End | Jump to first/last frame |
| G | Go to specific frame |
| R | Reset points |
| U | Undo last point |
| Enter/Space | Confirm selection |
| Escape | Cancel |

### Corner Ordering

Select corners in clockwise order starting from top-left:
1. Top-left (black spot end)
2. Top-right
3. Bottom-right (baulk end)
4. Bottom-left

### Output Format

```json
{
  "corners": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
  "frame_width": 1920,
  "frame_height": 1080,
  "source_path": "input.mp4",
  "calibration_frame": 1500
}
```

---

## Inference Pipelines

### Local Inference (GPU/CPU)

Performs detection using a local YOLOv8 model with automatic CUDA detection.

```bash
python run_local.py \
    --video <input.mp4> \
    --model <model.pt> \
    --calibration <calibration.json> \
    [--output <output_dir>] \
    [--chunk-minutes <float>] \
    [--frame-skip <int>] \
    [--confidence <float>] \
    [--player1 <name>] \
    [--player2 <name>]
```

To force CPU execution:
```bash
export CUDA_VISIBLE_DEVICES=-1  # Linux/macOS
set CUDA_VISIBLE_DEVICES=-1     # Windows
```

### Roboflow API

Cloud-based inference requiring no local GPU resources.

```bash
python run_roboflow.py \
    --video <input.mp4> \
    --api-key <roboflow_api_key> \
    [--calibration <calibration.json>] \
    [--model-id <workspace/model/version>] \
    [--detect-only]
```

API keys available at: https://app.roboflow.com/settings/api

### Local Inference Server

Self-hosted inference with Roboflow's inference package.

```bash
# Terminal 1: Start server
inference server start

# Terminal 2: Run pipeline
python run_roboflow.py --video <input.mp4> --local
```

### Optimized Pipeline (Smart Extraction)

Reduces API calls by 90%+ through motion-based frame selection.

```bash
# Full pipeline
python run_smart.py --video <input.mp4> --api-key <key>

# Extraction analysis only (no API calls)
python run_smart.py --video <input.mp4> --extract-only

# Cost comparison
python run_smart.py --video <input.mp4> --compare
```

**Extraction Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--sample-fps` | 5.0 | Temporal sampling rate for motion detection |
| `--motion-threshold` | 0.02 | Pixel delta threshold for motion classification |
| `--min-green` | 0.20 | Minimum green channel ratio for table detection |
| `--static-timeout` | 30.0 | Maximum interval between forced captures (seconds) |

---

## Cloud Deployment

The system supports Google Colab execution with automatic checkpointing for session resilience.

### Setup

```python
from google.colab import drive
drive.mount('/content/drive')

!pip install ultralytics supervision opencv-python matplotlib tqdm
```

### Execution

```python
import sys
sys.path.insert(0, '/content/drive/MyDrive/snooker-tracker')

from src.chunked_processing import run_chunked_pipeline

results = run_chunked_pipeline(
    video_path='/content/drive/MyDrive/match.mp4',
    model_path='/content/drive/MyDrive/models/best.pt',
    calibration_path='/content/drive/MyDrive/calibration.json',
    output_dir='/content/drive/MyDrive/output',
    chunk_minutes=3.0,
    frame_skip=1,
    player1="Player 1",
    player2="Player 2",
)
```

Processing automatically resumes from the last completed chunk on session reconnection.

---

## Model Training

### Dataset Preparation

```bash
# Extract and configure dataset
python training/setup_dataset.py \
    --zip <dataset.zip> \
    --output <dataset_dir>

# Analyze class distribution
python training/setup_dataset.py \
    --dataset <dataset_dir> \
    --analyze
```

Expected directory structure:
```
dataset/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── data.yaml
```

### Training

```bash
python training/train.py \
    --data <data.yaml> \
    [--model <n|s|m|l|x>] \
    [--epochs <int>] \
    [--batch <int>] \
    [--imgsz <int>] \
    [--device <cuda|cpu|0|1>] \
    [--resume <checkpoint.pt>]
```

**Model Variants:**

| Variant | Parameters | Inference Speed | GPU Memory |
|---------|------------|-----------------|------------|
| n | 3.2M | Fastest | ~4 GB |
| s | 11.2M | Fast | ~6 GB |
| m | 25.9M | Medium | ~8 GB |
| l | 43.7M | Slow | ~12 GB |
| x | 68.2M | Slowest | ~16 GB |

### Validation

```bash
python training/validate.py \
    --model <model.pt> \
    --data <data.yaml>
```

### Export

```bash
# ONNX (cross-platform)
python training/export_model.py --model <model.pt> --format onnx

# TensorRT (NVIDIA optimization)
python training/export_model.py --model <model.pt> --format engine --half

# Multiple formats
python training/export_model.py --model <model.pt> --format onnx torchscript tflite

# List supported formats
python training/export_model.py --list-formats
```

**Supported Export Formats:**

| Format | Target Platform | Requirements |
|--------|-----------------|--------------|
| onnx | Cross-platform | onnx |
| torchscript | PyTorch | — |
| engine | NVIDIA TensorRT | tensorrt |
| openvino | Intel | openvino |
| coreml | Apple | coremltools |
| tflite | Mobile/Edge | tensorflow |

---

## Validation Tools

### Position Map

Generates a static visualization of all tracked positions.

```bash
python validate_tracking.py \
    --mode positions \
    --tracking <tracking.json> \
    --output <output.png>
```

### Visual Comparison

Produces side-by-side frame/diagram comparisons.

```bash
python validate_tracking.py \
    --mode visual \
    --video <input.mp4> \
    --tracking <tracking.json> \
    --output <output_dir> \
    --frames "0,100,500"  # or "sample:20" or "all"
```

### Trajectory Analysis

Visualizes ball paths with anomaly detection.

```bash
python validate_tracking.py \
    --mode trajectory \
    --tracking <tracking.json> \
    --output <output.png> \
    [--no-anomalies]
```

### Ground Truth Comparison

Computes error metrics against labeled data.

```bash
python validate_tracking.py \
    --mode compare \
    --tracking <tracking.json> \
    --ground-truth <labels.json> \
    --output <output_dir>
```

---

## Output Specification

### Coordinate System

- **X-axis**: 0.0 (left cushion) → 1.0 (right cushion)
- **Y-axis**: 0.0 (black spot end) → 1.0 (baulk end)

### tracking.json

```json
{
  "total_frames": 5000,
  "active_tracks": 22,
  "pocketed_balls": 3,
  "tracks": {
    "<track_id>": {
      "track_id": 1,
      "color": "white",
      "first_frame": 0,
      "last_frame": 5000,
      "total_detections": 4800,
      "pocketed": false,
      "positions": [[x, y], ...]
    }
  },
  "frames": [
    {
      "frame_num": 0,
      "timestamp": 0.0,
      "balls": {
        "<track_id>": {
          "track_id": 1,
          "color": "white",
          "x": 0.5,
          "y": 0.7,
          "vx": 0.0,
          "vy": 0.0,
          "speed": 0.0
        }
      }
    }
  ]
}
```

### shots.json

```json
{
  "total_shots": 45,
  "shots": [
    {
      "shot_number": 1,
      "start_frame": 100,
      "end_frame": 200,
      "start_time": 4.0,
      "duration": 4.0,
      "cue_ball_path": [[x, y], ...],
      "balls_potted": ["red"],
      "first_contact": "red"
    }
  ]
}
```

### game_state.json

```json
{
  "player1": "Player 1",
  "player2": "Player 2",
  "scores": {"Player 1": 72, "Player 2": 45},
  "current_player": "Player 1",
  "reds_remaining": 12,
  "phase": "reds",
  "fouls": 2,
  "highest_break": {"Player 1": 45, "Player 2": 32}
}
```

---

## Command Reference

### run_local.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--video`, `-v` | path | required | Input video file |
| `--model`, `-m` | path | required | YOLOv8 weights (.pt) |
| `--calibration`, `-c` | path | required | Calibration file |
| `--output`, `-o` | path | `output/` | Output directory |
| `--chunk-minutes` | float | 3.0 | Processing chunk duration |
| `--frame-skip` | int | 1 | Frame subsampling factor |
| `--confidence` | float | 0.5 | Detection threshold |
| `--player1` | string | "Player 1" | First player name |
| `--player2` | string | "Player 2" | Second player name |
| `--calibrate` | flag | — | Run calibration mode |
| `--start-frame` | int | 0 | Calibration start frame |
| `--no-chunk` | flag | — | Disable chunked processing |

### run_roboflow.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--video`, `-v` | path | required | Input video file |
| `--api-key`, `-k` | string | — | Roboflow API key |
| `--local`, `-l` | flag | — | Use local inference server |
| `--model-id` | string | snooker-ball-detection-rnhxo/3 | Model identifier |
| `--calibration`, `-c` | path | — | Calibration file |
| `--output`, `-o` | path | `output/` | Output directory |
| `--chunk-minutes` | float | 3.0 | Processing chunk duration |
| `--frame-skip` | int | 2 | Frame subsampling factor |
| `--confidence` | float | 0.5 | Detection threshold |
| `--player1` | string | "Player 1" | First player name |
| `--player2` | string | "Player 2" | Second player name |
| `--calibrate` | flag | — | Run calibration mode |
| `--start-frame` | int | 0 | Calibration start frame |
| `--detect-only` | flag | — | Skip analysis phase |

### run_smart.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--video`, `-v` | path | required | Input video file |
| `--api-key`, `-k` | string | — | Roboflow API key |
| `--local`, `-l` | flag | — | Use local inference server |
| `--output`, `-o` | path | `output/` | Output directory |
| `--calibration`, `-c` | path | — | Calibration file |
| `--sample-fps` | float | 5.0 | Motion sampling rate |
| `--motion-threshold` | float | 0.02 | Motion sensitivity |
| `--min-green` | float | 0.20 | Table detection threshold |
| `--static-timeout` | float | 30.0 | Forced capture interval |
| `--confidence` | float | 0.5 | Detection threshold |
| `--extract-only` | flag | — | Run extraction only |
| `--skip-extraction` | flag | — | Use existing candidates |
| `--candidates` | path | — | Candidates file path |
| `--detect-only` | flag | — | Skip analysis phase |
| `--compare` | flag | — | Run comparison analysis |
| `--player1` | string | "Player 1" | First player name |
| `--player2` | string | "Player 2" | Second player name |

### validate_tracking.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--mode` | enum | required | positions\|visual\|trajectory\|compare |
| `--tracking` | path | required | Tracking data file |
| `--output` | path | required | Output path |
| `--video` | path | — | Input video (visual mode) |
| `--frames` | string | "0,100,200" | Frame selection |
| `--ground-truth` | path | — | Ground truth file (compare mode) |
| `--no-anomalies` | flag | — | Disable anomaly detection |

### training/train.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--data` | path | required | Dataset configuration |
| `--epochs` | int | 100 | Training epochs |
| `--batch` | int | 16 | Batch size |
| `--imgsz` | int | 640 | Input resolution |
| `--model` | enum | n | Model variant (n/s/m/l/x) |
| `--patience` | int | 10 | Early stopping patience |
| `--device` | string | auto | Compute device |
| `--project` | path | — | Project directory |
| `--name` | string | — | Run name |
| `--resume` | path | — | Resume checkpoint |
| `--workers` | int | 8 | Data loader workers |

---

## Troubleshooting

### CUDA Memory Errors

Reduce memory consumption:
- Decrease batch size: `--batch 8`
- Use smaller model variant: `--model n`
- Reduce input resolution: `--imgsz 480`
- Force CPU execution: `--device cpu`

### Module Import Errors

```bash
# Missing ultralytics
pip install ultralytics

# Missing supervision
pip install supervision

# Missing inference
pip install inference
```

### Inference Server Connection Failed

Ensure the server is running:
```bash
inference server start
```

### Calibration Accuracy Issues

- Navigate to a frame with clear table visibility
- Ensure all pocket positions are visible
- Place points precisely at pocket edges
- Use `--start-frame` to select optimal frame

### Tracking Identity Instability

- Increase detection confidence: `--confidence 0.6`
- Reduce frame skip: `--frame-skip 1`
- Verify calibration accuracy

### API Authentication Errors (401/403)

- Verify API key validity
- Check account quota at https://app.roboflow.com

---

## Class Definitions

| Class ID | Color | Point Value | Quantity |
|----------|-------|-------------|----------|
| 0 | White | — | 1 (cue ball) |
| 1 | Red | 1 | 15 |
| 2 | Yellow | 2 | 1 |
| 3 | Green | 3 | 1 |
| 4 | Brown | 4 | 1 |
| 5 | Blue | 5 | 1 |
| 6 | Pink | 6 | 1 |
| 7 | Black | 7 | 1 |

---

## Project Structure

```
snooker-tracker/
├── config/
│   ├── settings.py              # Configuration parameters
│   └── classes.py               # Data structures and enumerations
├── src/
│   ├── calibration.py           # Homography estimation
│   ├── coordinates.py           # Coordinate transformation
│   ├── detection.py             # YOLOv8 inference wrapper
│   ├── tracking.py              # ByteTrack integration
│   ├── shot_detection.py        # Shot boundary detection
│   ├── game_state.py            # Rules engine
│   ├── play_by_play.py          # Commentary generation
│   ├── visualization.py         # Plotting utilities
│   ├── chunked_processing.py    # Resumable batch processing
│   ├── roboflow_detection.py    # Roboflow API client
│   └── smart_extraction.py      # Motion-based frame selection
├── training/
│   ├── setup_dataset.py         # Dataset preparation
│   ├── train.py                 # Training script
│   ├── validate.py              # Validation script
│   └── export_model.py          # Model export utilities
├── run_local.py                 # Local inference pipeline
├── run_roboflow.py              # Roboflow inference pipeline
├── run_smart.py                 # Optimized inference pipeline
├── validate_tracking.py         # Validation tools
└── output/                      # Default output directory
```

---

## References

- Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLOv8. https://github.com/ultralytics/ultralytics
- Zhang, Y., et al. (2022). ByteTrack: Multi-Object Tracking by Associating Every Detection Box. ECCV 2022.
- Roboflow. (2023). Inference: An open-source computer vision inference server. https://github.com/roboflow/inference

---

## License

This software is provided for research and educational purposes.
