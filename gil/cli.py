import logging
import pickle
from hashlib import sha1
from pathlib import Path
from typing import Any, Union

import typer
from rich import print
from rich.logging import RichHandler

from gil import paths
from gil.core import Blob, Commit, Sha, Tree
from gil.utils import NoRefException, get_ref, set_ref

FORMAT = "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger(__name__)

app = typer.Typer(help="`gil` is a git-like tool for educational purposes.")


########################################################################################
@app.command()
def init():
    """Create a gil repo."""
    pass
    path = Path.cwd() / ".gil"
    if path.exists():
        logger.warning(f"gil repo at {path} already exists")
        return

    path.mkdir()
    (path / "objects").mkdir()
    (path / "refs").mkdir()
    (path / "refs/tags").mkdir()
    (path / "refs/heads").mkdir()
    (path / "refs/remotes").mkdir()
    with (path / "HEAD").open("w") as f:
        f.write("refs/heads/main")
    logger.info(f"gil repo created in '{path}'")


########################################################################################
# BLOB
@app.command()
def hash_object(path: Path):
    """Hash the object and add it to the repo."""
    assert path.is_file()
    data = path.read_bytes()
    sha = hash_data(data)
    dump_obj(sha, Blob(data), path)
    return sha


@app.command()
def cat_file(sha: str, do_print: bool = True):
    """Read the content of the object with the given sha."""
    path = paths.OBJECTS_DIR / sha
    assert path.is_file()
    with path.open("rb") as f:
        obj = pickle.load(f)
    if do_print:
        print(obj)
    return obj


########################################################################################
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


########################################################################################
# COMMIT
@app.command()
def snapshot(commit_message: str):
    """Think: git add and git commit"""
    tree_sha = hash_tree(Path("."))

    try:
        prev_commit_sha = get_ref()
        _prev_commit = cat_file(prev_commit_sha, do_print=False)
        if _prev_commit.tree == tree_sha:
            logger.warning("Nothing changed, nothing to commit.")
            return
    except NoRefException:
        prev_commit_sha = ""

    commit = Commit(tree_sha, prev_commit_sha, commit_message)
    commit_sha = hash_data((str(commit.parent) + commit.tree).encode())
    dump_obj(commit_sha, commit, "commit")
    set_ref(commit_sha)


########################################################################################
# MISC
@app.command()
def log():
    """log of all commits"""
    commit_sha = get_ref()
    while commit_sha:
        commit: Commit = cat_file(commit_sha, do_print=False)
        print(f"# {commit_sha}")
        print(commit)
        commit_sha = commit.parent


# GRAPH
@app.command()
def graph():
    from graphviz import Digraph

    dot = Digraph()
    for path in paths.OBJECTS_DIR.iterdir():
        sha = path.name
        obj = cat_file(sha)

        if isinstance(obj, Blob):
            dot.node(sha[:8], shape="box")
        elif isinstance(obj, Tree):
            dot.node(sha[:8], shape="triangle")
            for child_sha, child_name in obj.items:
                dot.edge(sha[:8], child_sha[:8], child_name)
        elif isinstance(obj, Commit):
            dot.node(sha[:8], shape="circle")
            dot.edge(sha[:8], obj.tree[:8], obj.commit_message)
            dot.edge(sha[:8], obj.parent[:8], obj.commit_message)
        else:
            raise ValueError("WTF?")

    dot.render("/tmp/gil.pdf", view=True)


########################################################################################
# UTILS
def dump_obj(sha: Sha, obj: Any, message) -> None:
    dst = paths.OBJECTS_DIR / sha
    if dst.exists():
        logger.warning(f"{sha} --> '{message}' already hashed")
    else:
        with dst.open("wb") as f:
            pickle.dump(obj, f)
        logger.info(f"{sha} --> '{message}' hashed")


def hash_data(data: Union[str, bytes]) -> Sha:
    if isinstance(data, str):
        data = data.encode()
    return sha1(data).hexdigest()


########################################################################################
if __name__ == "__main__":
    app()
