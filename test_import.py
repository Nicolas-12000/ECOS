import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("PYTHONPATH:", sys.path[:5])
print()

try:
    from app.main import app
    print("✓ App imported successfully!")
    print()
    print("✓ Endpoints:")
    for route in app.routes:
        print(f"  - {route.path}")
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
