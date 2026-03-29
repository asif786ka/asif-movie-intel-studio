"""Production startup script with diagnostic logging."""
import sys
import os
import time

sys.stdout.write("=== Python startup script beginning ===\n")
sys.stdout.flush()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def timed_import(name):
    start = time.time()
    sys.stdout.write(f"Importing {name}... ")
    sys.stdout.flush()
    try:
        __import__(name)
        elapsed = time.time() - start
        sys.stdout.write(f"OK ({elapsed:.1f}s)\n")
        sys.stdout.flush()
    except Exception as e:
        elapsed = time.time() - start
        sys.stdout.write(f"FAILED ({elapsed:.1f}s): {e}\n")
        sys.stdout.flush()
        return False
    return True

ok = True
ok = timed_import("fastapi") and ok
ok = timed_import("uvicorn") and ok
ok = timed_import("numpy") and ok
ok = timed_import("pydantic") and ok
ok = timed_import("httpx") and ok

sys.stdout.write("Core imports done, starting app import...\n")
sys.stdout.flush()

try:
    start = time.time()
    from app.main import app
    elapsed = time.time() - start
    sys.stdout.write(f"App imported in {elapsed:.1f}s\n")
    sys.stdout.flush()
except Exception as e:
    sys.stdout.write(f"App import failed: {e}\n")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.exit(1)

sys.stdout.write("Starting uvicorn...\n")
sys.stdout.flush()

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
