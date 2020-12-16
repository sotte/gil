from pathlib import Path
from gil.core import Sha


def get_root_path() -> Path:
    return Path(__file__).parent.parent.absolute()


def get_demo_repo_path() -> Path:
    return get_root_path() / "demo_repo"


def get_object_dir() -> Path:
    return get_root_path() / "gil_objects/objects"


def get_gil_dir() -> Path:
    return get_root_path() / "gil_objects"


def get_HEAD_path() -> Path:
    return get_gil_dir() / "HEAD"


def get_HEAD() -> Sha:
    with get_HEAD_path().open("r") as f:
        return f.read()


if __name__ == "__main__":
    print(get_root_path())
