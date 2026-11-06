"""Bound exact path arguments below platform command-line limits."""


def path_batches(paths, budget=4096):
    """Keep order and literal paths; never broaden a selection to the repository.

    UTF-16 units plus quoting overhead are conservative for Windows and remain
    small on POSIX. Each caller still validates individual relative paths.
    """
    batch, used = [], 0
    for path in paths:
        size = len(path.encode('utf-16-le')) // 2 + path.count('"') + path.count('\\') + 3
        if batch and used + size > budget:
            yield batch
            batch, used = [], 0
        batch.append(path)
        used += size
    if batch:
        yield batch
