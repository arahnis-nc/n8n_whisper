from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"

for path in (str(ROOT), str(SERVICES)):
    if path not in sys.path:
        sys.path.insert(0, path)
