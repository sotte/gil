from pathlib import Path
import pickle
from typing import Any

import typer
from wasabi import Printer

from gil.utils import get_ref, set_ref, NoRefException
from gil.core import Blob, Tree, Commit, hash_data, Sha
from gil import paths


app = typer.Typer()
msg = Printer(line_max=220)


@app.command()
def init():
    """Create a gil repo."""
    path = Path.cwd() / ".gil"
    if path.exists():
        msg.warn(f"gil repo at {path} already exists")
        return

    path.mkdir()
    (path / "objects").mkdir()
    (path / "refs").mkdir()
    (path / "refs/tags").mkdir()
    (path / "refs/heads").mkdir()
    (path / "refs/remotes").mkdir()
    with (path / "HEAD").open("w") as f:
        f.write("refs/heads/main")
    msg.good(f"gil repo created in '{path}'")


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
    path = paths.OBJECTS_DIR / sha
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
    sha = hash_data("".join(sha for sha, _ in items))
    dump_obj(sha, Tree(items), path)

    return sha


# COMMIT
@app.command()
def commit(commit_message: str):
    """gil add and gil commit"""
    tree_sha = hash_tree(Path("."))
    try:
        prev_commit_sha = get_ref()
        prev_commit = cat_file(prev_commit_sha, do_print=False)
        if prev_commit.tree == tree_sha:
            msg.warn("Nothing changed, nothing to commit.")
            return
    except NoRefException:
        prev_commit_sha = ""

    commit = Commit(tree_sha, prev_commit_sha, commit_message)
    commit_sha = hash_data((str(commit.parent) + commit.tree).encode())
    dump_obj(commit_sha, commit, "commit")

    set_ref(commit_sha)


@app.command()
def log():
    """log of all commits"""
    commit_sha = get_ref()
    while commit_sha:
        commit = cat_file(commit_sha, do_print=False)
        commit_sha = commit.parent
        print(" * ", commit_sha)
        print("   ", commit)


# UTILS
def dump_obj(sha: Sha, obj: Any, message) -> None:
    dst = paths.OBJECTS_DIR / sha
    if dst.exists():
        msg.warn(f"{sha} --> '{message}' already hashed")
    else:
        with dst.open("wb") as f:
            pickle.dump(obj, f)
        msg.info(f"{sha} --> '{message}' hashed")


if __name__ == "__main__":
    app()
