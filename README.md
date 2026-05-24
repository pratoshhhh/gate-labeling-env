 # Gate Labeling Project

 This repository contains scripts and labelled data for gate pose detection and labeling using Label Studio.

 ## Project overview
 - `convert_dataset.py`: helper to convert/export datasets
 - `label_studio_config.xml`: Label Studio labeling config
 - `project_export.json`: exported tasks for Label Studio
 - `yolov8_gate_pose/`: images and dataset structure for YOLOv8
 - `labels/`: label files for training/validation

 ## Requirements
 - Python 3.8+ (virtualenv recommended)

 ## Setup (Windows)
 1. Activate the virtual environment:

    Powershell:

    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
    & label_env\Scripts\Activate.ps1
    ```

    CMD:

    ```cmd
    label_env\Scripts\activate.bat
    ```

 2. Install dependencies (if you maintain a `requirements.txt`):

    ```powershell
    pip install -r requirements.txt
    # or, to install Label Studio directly:
    pip install label-studio
    ```

 ## Running Label Studio
 1. Start Label Studio server:

    ```powershell
    label-studio start --host 0.0.0.0 --port 8080
    ```

 2. Open your browser at `http://localhost:8080` and create a new project.
 3. To import the provided project export, use the project import UI and select `project_export.json`.
 4. To use the labeling configuration, during project setup choose `label_studio_config.xml` as the labeling config (or paste its contents in the UI).

 ## Dataset layout
 - `yolov8_gate_pose/images/train` and `yolov8_gate_pose/images/val` — images for training/validation
 - `labels/train` and `labels/val` — corresponding label files

 ## Committing files (exclude virtualenv)
 Make sure the `label_env` virtual environment is not committed. A recommended `.gitignore` is included.

 Quick git commands (run from the repo root):

 ```powershell
 # Remove virtualenv from git if it was previously tracked
 git rm -r --cached label_env || $true
 # Add the README and .gitignore and commit
 git add README.md .gitignore
 git add -A
 git commit -m "Add README and .gitignore; exclude virtualenv"
 ```

 If this is a new repository, initialize first:

 ```powershell
 git init
 ```

 ## Notes
 - The virtual environment directory is `label_env/` — do not commit it.
 - If you want help generating `requirements.txt`, I can run `pip freeze` inside the venv and create it.
