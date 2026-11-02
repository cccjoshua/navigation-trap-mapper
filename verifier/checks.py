"""Checks shared by the tool verifiers. Pure functions of their arguments."""

import re
from collections import deque

PAGE_ID = re.compile(r"^p\d{2}$")
START = "p00"
MAX_SEED = 1_000_000
MAX_PAGES = 20


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def seed_problem(seed):
    if not 0 <= seed <= MAX_SEED:
        return f"seed must be between 0 and {MAX_SEED}"
    return None


def page_problem(page_id):
    if not PAGE_ID.fullmatch(page_id):
        return f"{page_id!r} is not a page id like p00"
    return None


def reached(start, links):
    """Every page reachable from ``start`` in ``links`` (page -> the pages it links to)."""
    seen, queue = {start}, deque([start])
    while queue:
        for there in links.get(queue.popleft(), []):
            if there not in seen:
                seen.add(there)
                queue.append(there)
    return seen


def traps(graph):
    """The trap pages of a contract GraphOutput: reachable from the start, unable to reach the target."""
    links = {page.page_id: page.links for page in graph.pages}
    backward = {page: [] for page in links}
    for page, found in links.items():
        for there in found:
            backward.setdefault(there, []).append(page)
    return reached(graph.start_page_id, links) - reached(graph.target_page_id, backward)
