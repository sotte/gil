from pathlib import Path
import pickle
from typing import Any

import typer
from wasabi import Printer

from gil.utils import get_root_path, get_object_dir, get_ref, set_ref, NoRefException
from gil.core import Blob, Tree, Commit, hash_data, Sha


app = typer.Typer()
msg = Printer(line_max=220)


@app.command()
def init():
    """Create a gil repo."""
    gil_object_path = get_root_path() / "gil_objects"
    if gil_object_path.exists():
        msg.warn(f"gil repo at {gil_object_path} already exists")
        return

    gil_object_path.mkdir(exist_ok=True)
    (gil_object_path / "objects").mkdir(exist_ok=True)
    msg.good(f"gil repo created in {gil_object_path}")


# BLOB
@app.command()
def hash_object(path: Path):
    """hash the object and add it to the repo."""
    assert path.is_file()

    with path.open("rb") as f:
        data = f.read()
    sha = hash_data(data)
    dump_obj(sha, Blob(data), path)

    return sha


@app.command()
def cat_file(sha: str, do_print: bool = True):
    """Read the content of the file for the given sha."""
    path = get_object_dir() / sha
    assert path.is_file()

    with path.open("rb") as f:
        obj = pickle.load(f)

    if do_print:
        print(obj)
    return obj


# TREE
@app.command()
def hash_tree(path: Path):
    """Hash the tree (recursively) and add it to the repo."""
    assert path.is_dir()

    # collect all the data
    items = []
    for p in path.iterdir():
        if p.name == ".gil":
            continue
        elif p.is_file():
            items.append((hash_object(p), str(p.name)))
        elif p.is_dir():
            items.append((hash_tree(p), str(p.name)))
        else:
            raise Exception("WTF!")

    # create and dump tree object
    items = sorted(items)
    sha = hash_data("".join(sha for sha, _ in items).encode())
    dump_obj(sha, Tree(items), path)

    return sha


# COMMIT
@app.command()
def commit(commit_message: str):
    """gil add and gil commit"""
    tree_sha = hash_tree(Path("."))
    try:
        prev_commit_sha = get_ref("HEAD")
        prev_commit = cat_file(prev_commit_sha, do_print=False)
        if prev_commit.tree == tree_sha:
            msg.warn("Nothing changed, nothing to commit.")
            return
    except NoRefException:
        prev_commit_sha = ""

    commit = Commit(tree_sha, prev_commit_sha, commit_message)
    commit_sha = hash_data((str(commit.parent) + commit.tree).encode())
    dump_obj(commit_sha, commit, "commit")

    set_ref(commit_sha, "HEAD")


# UTILS
def dump_obj(sha: Sha, obj: Any, message) -> None:
    dst = get_object_dir() / sha
    if dst.exists():
        msg.info(f"Already hashed '{message}' --> {sha}")
    else:
        with dst.open("wb") as f:
            pickle.dump(obj, f)
        msg.info(f"Hashed '{message}' --> {sha}")


if __name__ == "__main__":
    app()
