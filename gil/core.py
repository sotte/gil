from typing import List, Tuple
from dataclasses import dataclass
from hashlib import sha1


# DTYPES
Sha = str


# CORE DTYPES
@dataclass
class Blob:
    data: bytes


@dataclass
class Tree:
    items: List[Tuple[Sha, str]]


@dataclass
class Commit:
    tree: Sha
    parent: Sha
    commit_message: str
    committer: str = "Stefan :)"


def hash_data(data) -> Sha:
    if isinstance(data, str):
        data = data.encode()
    return sha1(data).hexdigest()
