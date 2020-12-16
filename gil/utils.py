from pathlib import Path
from gil.core import Sha


class NoRefException(Exception):
    pass


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


def get_ref(name="HEAD") -> Sha:
    try:
        with (get_gil_dir() / name).open("r") as f:
            return f.read()
    except FileNotFoundError:
        raise NoRefException


def set_ref(sha: Sha, name: str = "HEAD") -> None:
    assert name == "HEAD" or name.startswith("tag/") or name.startswith("branch/")
    with (get_gil_dir() / name).open("w") as f:
        f.write(sha)


def set_HEAD(sha: Sha) -> None:
    with get_HEAD_path().open("w") as f:
        f.write(sha)


if __name__ == "__main__":
    print(get_root_path())
