import os
import json
import random
import shutil

# =====================================================================
# 1. PATH CONFIGURATION
# =====================================================================
JSON_PATH = "project_export.json"
SRC_IMAGES_DIR = "raw_images"
OUTPUT_DATASET_DIR = "yolov8_gate_pose"
TRAIN_RATIO = 0.8  

# Nuke old directories to prevent file pollution
if os.path.exists(OUTPUT_DATASET_DIR):
    shutil.rmtree(OUTPUT_DATASET_DIR)

for phase in ["train", "val"]:
    os.makedirs(os.path.join(OUTPUT_DATASET_DIR, f"images/{phase}"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DATASET_DIR, f"labels/{phase}"), exist_ok=True)

with open(JSON_PATH, 'r') as f:
    tasks = json.load(f)

processed_records = []

# =====================================================================
# 2. PARSE TASKS WITH GEOMETRIC MULTI-OBJECT MATCHING
# =====================================================================
for task in tasks:
    uploaded_file = task['data']['image']
    if str(uploaded_file).startswith('/data/upload/'):
        filename = uploaded_file.split('?')[0].split('/')[-1].split('-', 1)[-1]
    else:
        filename = os.path.basename(uploaded_file)
        
    src_img_path = os.path.join(SRC_IMAGES_DIR, filename)
    if not os.path.exists(src_img_path):
        continue  

    annotations = task.get('annotations', [])
    if not annotations or not (results := annotations[0].get('result', [])):
        continue

    img_w = results[0]['original_width']
    img_h = results[0]['original_height']

    detected_boxes = []
    detected_points = []

    # Step A: Parse bounding boxes and keypoints separately 
    for res in results:
        res_type = res['type']
        val = res['value']
        
        if res_type == 'rectanglelabels':
            # Extract boundaries for strict point-in-box spatial filtering
            xmin, ymin = val['x'] / 100.0, val['y'] / 100.0
            w, h = val['width'] / 100.0, val['height'] / 100.0
            xmax, ymax = xmin + w, ymin + h
            
            # Map parameters directly to standard YOLO relative sizing format
            cx, cy = xmin + (w / 2.0), ymin + (h / 2.0)
            detected_boxes.append({
                'bounds': (xmin, ymin, xmax, ymax),
                'yolo_box': (cx, cy, w, h),
                'assigned_kpts': {}
            })
            
        elif res_type == 'keypointlabels':
            label = val['keypointlabels'][0]
            kx, ky = val['x'] / 100.0, val['y'] / 100.0
            vis = 1 if val.get('hidden', False) else 2
            detected_points.append({'label': label, 'coords': (kx, ky, vis)})

    # Step B: Associate loose keypoints to their respective bounding box spaces
    for pt in detected_points:
        kx, ky, kv = pt['coords']
        best_box = None
        min_distance_to_center = float('inf')
        
        for box in detected_boxes:
            xmin, ymin, xmax, ymax = box['bounds']
            # Intersection test: Is the point strictly bounded inside this gate?
            if xmin <= kx <= xmax and ymin <= ky <= ymax:
                cx, cy, _, _ = box['yolo_box']
                dist = (kx - cx)**2 + (ky - cy)**2 # Proximity distance fallback
                if dist < min_distance_to_center:
                    min_distance_to_center = dist
                    best_box = box
                    
        # Fallback safeguard: If a point floats slightly outside box lines, map to nearest gate center
        if not best_box and detected_boxes:
            for box in detected_boxes:
                cx, cy, _, _ = box['yolo_box']
                dist = (kx - cx)**2 + (ky - cy)**2
                if dist < min_distance_to_center:
                    min_distance_to_center = dist
                    best_box = box

        if best_box:
            best_box['assigned_kpts'][pt['label']] = (kx, ky, kv)

    # Step C: Format data into standard multi-line text entries
    yolo_lines = []
    for box in detected_boxes:
        cx, cy, nw, nh = box['yolo_box']
        points = box['assigned_kpts']
        kp_string = ""
        
        # Sequentially map required pose positions
        for lbl in ["TL", "TR", "BR", "BL"]:
            if lbl in points:
                kx, ky, kv = points[lbl]
                kp_string += f" {kx:.6f} {ky:.6f} {kv}"
            else:
                kp_string += " 0.000000 0.000000 0"
                
        yolo_lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}{kp_string}\n")

    if yolo_lines:
        processed_records.append((filename, src_img_path, yolo_lines))

# =====================================================================
# 3. BALANCED SHUFFLE & DATASET DEPLOYMENT
# =====================================================================
random.seed(42)
random.shuffle(processed_records)

split_idx = int(len(processed_records) * TRAIN_RATIO)
splits = {"train": processed_records[:split_idx], "val": processed_records[split_idx:]}

for phase, records in splits.items():
    for name, s_path, lines in records:
        base = os.path.splitext(name)[0]
        # Move raw image files over to targeted dataset splits
        shutil.copy(s_path, os.path.join(OUTPUT_DATASET_DIR, f"images/{phase}", name))
        
        # Write individual multi-line text files mirroring our bounding arrays
        with open(os.path.join(OUTPUT_DATASET_DIR, f"labels/{phase}", f"{base}.txt"), "w") as lf:
            lf.writelines(lines)

print("-" * 50)
print(f"✓ Success! Processed all overlapping and multi-gate images.")
print(f"Output Directory Location: '{OUTPUT_DATASET_DIR}'")
print(f"Dataset Metrics -> Train Phase: {len(splits['train'])} | Validation Phase: {len(splits['val'])}")
print("-" * 50)