# `gil` is a git-like for educational purposes

This project implements some core git concepts in simple readable python.

Some keywords:

- content-adressable storage
- merkle graph
- https://git-scm.com/book/en/v2/Git-Internals-Git-Objects


## Setup and Usage
```bash
poetry shell
poetry install

cd demo_repo

gil init

# Hashing files/blobs
gil hash-object hello.txt

gil cat-file 648a6a6ffffdaa0badb23b8baf90b6168dd16b3a

# hashing the same file does not do anything
gil hash-object hello.txt


# Hashing trees
gil hash-tree folder/subfolder


# add and commit -> snapshot
gil snapshot

```
