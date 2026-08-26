"""
Standalone seed runner.
Usage:  python -m app.seed   OR   python scripts/seed_data.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.seed import run_seed

if __name__ == "__main__":
    run_seed()
