import os
import time

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
MAX_AGE_SECONDS = 24 * 60 * 60  # 1 day

now = time.time()

for filename in os.listdir(UPLOAD_FOLDER):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(file_path):
        file_age = now - os.path.getmtime(file_path)
        if file_age > MAX_AGE_SECONDS:
            try:
                os.remove(file_path)
                print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
