from dataclasses import dataclass
from typing import List, Tuple

# DTYPES
Sha = str

# CORE DTYPES
@dataclass
class Blob:
    """A blob of data - binary large object."""
    data: bytes


@dataclass
class Tree:
    """A folder - pointing to Blobs and Trees."""
    items: List[Tuple[Sha, str]]


@dataclass
class Commit:
    """Point to a tree and a previous commit (plus some metadata)."""
    tree: Sha
    parent: Sha
    commit_message: str
    committer: str = "Stefan :)"
