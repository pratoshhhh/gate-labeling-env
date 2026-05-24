
# gate-labeling-env

This repository contains two helper files used to convert Label Studio exports into a YOLOv8-style dataset with per-object keypoints:

- `convert_dataset.py` — converts `project_export.json` (Label Studio export) + local images into a YOLOv8-compatible dataset that embeds keypoints per object.
- `project_export.json` — Label Studio project export (already contains detections with keypoints and YOLO-style annotations produced from labeling).

The JSON contains keypoint labels (e.g., `TL`, `TR`, `BR`, `BL`) and bounding boxes; `convert_dataset.py` associates keypoints to their parent bounding boxes and emits the combined YOLO+keypoint text files.

Requirements
- Python 3.8+
- (optional) a virtual environment. Example:

```powershell
python -m venv label_env
& label_env\Scripts\Activate.ps1
pip install -r requirements.txt  # if you create one
```

How it works
- `convert_dataset.py` reads `project_export.json` (the Label Studio export) and expects the referenced images to be available in `raw_images/`.
- For each task it extracts rectangle (bounding box) and keypoint annotations, assigns keypoints to the nearest/containing bounding box (labels TL/TR/BR/BL), then writes one `.txt` label file per image in `yolov8_gate_pose/labels/{train|val}/` with the following line format:

  class cx cy w h TL_x TL_y TL_v TR_x TR_y TR_v BR_x BR_y BR_v BL_x BL_y BL_v

- It also copies the referenced images into `yolov8_gate_pose/images/{train|val}/` and splits the dataset with an 80/20 train/val ratio by default.

Quick usage
1. Make sure your images referenced in `project_export.json` are located inside `raw_images/` (filenames must match the exported paths).
2. Run the converter:

```powershell
python convert_dataset.py
```

On success you'll see an output like:

```
✓ Success! Processed all overlapping and multi-gate images.
Output Directory Location: 'yolov8_gate_pose'
Dataset Metrics -> Train Phase: N | Validation Phase: M
```

Using the output with YOLOv8
- Create a simple `data.yaml` for Ultralytics YOLO training (example):

```yaml
path: yolov8_gate_pose
train: images/train
val: images/val
nc: 1
names: ["gate"]
```

- Install Ultralytics and train (example):

```powershell
pip install ultralytics
yolo task=detect mode=train model=yolov8n.pt data=data.yaml epochs=50
```

Notes about keypoints
- The produced label files include four ordered keypoints (`TL`, `TR`, `BR`, `BL`) after the standard YOLO box fields. If a keypoint is missing it's written as `0.000000 0.000000 0`.
- If you use a custom training loop or architecture that consumes keypoints, adapt the data loader to parse the extended label format.

Customizing the conversion
- Edit the top of `convert_dataset.py` to change `JSON_PATH`, `SRC_IMAGES_DIR`, `OUTPUT_DATASET_DIR`, or `TRAIN_RATIO`.
- The script matches keypoints to boxes by containment first, then by proximity to box centers as a fallback.
