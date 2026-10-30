LIKE_ESCAPE = "\\"


def contains_pattern(query: str) -> str:
    """Build a LIKE pattern that matches names containing the raw query.

    `%` and `_` are wildcards in LIKE, so they are escaped to make sure a user
    searching for "50%" does not match everything.
    """
    escaped = (
        query.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2)
        .replace("%", LIKE_ESCAPE + "%")
        .replace("_", LIKE_ESCAPE + "_")
    )
    return f"%{escaped}%"
