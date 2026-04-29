import sys
import os
print(f"CWD: {os.getcwd()}")
print(f"sys.path: {sys.path}")
try:
    from app.main import app
    print("Found app.main")
    print(f"app file: {app.__file__ if hasattr(app, '__file__') else 'unknown'}")
except Exception as e:
    print(f"Error importing app: {e}")
