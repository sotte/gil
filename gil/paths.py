from pathlib import Path


def _gil_root():
    path = Path.cwd()
    for _ in range(10):
        if (path / ".gil").exists():
            return path
        path = path.parent


REPO_ROOT = _gil_root()
if REPO_ROOT:
    GIL_ROOT = REPO_ROOT / ".gil"
    OBJECTS_DIR = REPO_ROOT / ".gil/objects"
    HEAD_FILE = REPO_ROOT / ".gil/HEAD"
