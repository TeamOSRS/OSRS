file_path = r"E:\Projects\OSRS\OSRS\ArmSyncedMovementUpdatedV2\gui.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    line_stripped = line.strip()
    if any(k in line_stripped for k in ["chiman_calibration.json", "calib", "save_calib", "load_calib"]):
        print(f"{idx+1}: {line_stripped}")
