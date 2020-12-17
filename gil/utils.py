from gil.core import Sha
from gil import paths


class NoRefException(Exception):
    pass


def get_ref() -> Sha:
    with paths.HEAD_FILE.open("r") as f:
        name = f.read()
    try:
        with (paths.GIL_ROOT / name).open("r") as f:
            return f.read()
    except FileNotFoundError:
        raise NoRefException


def set_ref(sha: Sha) -> None:
    with paths.HEAD_FILE.open("r") as f:
        name = f.read()
    with (paths.GIL_ROOT / name).open("w") as f:
        f.write(sha)
