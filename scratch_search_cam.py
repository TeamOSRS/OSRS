import os

for root, dirs, files in os.walk("E:\\Projects\\OSRS\\OSRS"):
    if "node_modules" in root or ".git" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "width" in content.lower() or "height" in content.lower() or "resolution" in content.lower():
                    # Print lines
                    lines = content.splitlines()
                    for idx, line in enumerate(lines):
                        if any(w in line for w in ["width", "height", "resolution", "640", "480", "320", "240", "160", "120"]):
                            print(f"{file}:{idx+1}: {line.strip()}")
            except Exception:
                pass
