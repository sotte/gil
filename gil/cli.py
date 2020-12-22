from pathlib import Path
import pickle
from typing import Any

import typer
from wasabi import Printer

from gil import paths
from gil.core import Blob, Commit, Sha, Tree, hash_data
from gil.utils import NoRefException, get_ref, set_ref


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
    """Hash the object and add it to the repo."""
    assert path.is_file()

    with path.open("rb") as f:
        data = f.read()
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
    """Think: git add and git commit"""
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
        print(" *", commit_sha)
        print("  ", commit)
        commit_sha = commit.parent


# GRAPH
@app.command()
def graph():
    """Graphviz graph of the current repo."""
    from graphviz import Digraph

    dot = Digraph()
    commit_sha = get_ref()
    while commit_sha:
        commit = cat_file(commit_sha, do_print=False)
        dot.node(commit_sha[:8])

        dot.node(commit.tree[:8], shape="triangle")
        dot.edge(commit_sha[:8], commit.tree[:8])

        tree = cat_file(commit.tree)
        _graph_subtree(commit.tree, tree, dot)

        parent_sha = commit.parent
        if parent_sha:
            dot.edge(parent_sha[:8], commit_sha[:8])

        commit_sha = parent_sha

    dot.render("/tmp/gil.pdf", view=True)


def _graph_subtree(tree_sha: Sha, tree: Tree, dot):
    for sha, path in tree.items:
        obj = cat_file(sha)
        if isinstance(obj, Tree):
            dot.node(sha[:8], shape="triangle")
            _graph_subtree(sha, tree=obj, dot=dot)
        else:
            dot.node(sha[:8], shape="box")
        dot.edge(tree_sha[:8], sha[:8], path)


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
