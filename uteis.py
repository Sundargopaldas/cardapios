import os
import re
from datetime import datetime

log_dir = "log"
log_file = os.path.join(log_dir, "log.txt")

os.makedirs(log_dir, exist_ok=True)

if os.path.exists(log_file):
    os.remove(log_file)

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(linha)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)