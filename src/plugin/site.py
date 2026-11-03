"""The simulated website: a link graph built from a seed alone.

A core of pages runs from the start to the target, each linking on to the next and to a few other
core pages, so every core page reaches the target. Trap clusters hang off the core: a two-page loop,
a three-page ring, a page with no links, and a funnel page whose links lead only into another trap.
A few pages link into the core but no page links to them, so they are unreachable from the start.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass
from itertools import pairwise

START = "p00"
MAX_SEED = 1_000_000
TITLES = (
    "Account Overview", "Activity Log", "Billing History", "Data Export", "Device List", "Help Center",
    "Invoice Archive", "Message Inbox", "Notification Rules", "Order Status", "Payment Methods", "Plan Upgrade",
    "Privacy Center", "Project Board", "Report Builder", "Saved Searches", "Security Keys", "Shipping Details",
    "Support Ticket", "Team Members", "Usage Summary", "Workspace Settings", "Audit Trail", "API Tokens",
    "Calendar Sync", "Coupon Center", "Download Hub", "Event Feed", "File Browser", "Guest Access",
)
TRAP_KINDS = ("loop", "ring", "sink", "funnel")
MAX_DEPTH = 6  # every reachable page is at most this many links from the start
MAX_PAGES = 40  # the most pages one list_links call shows


@dataclass(frozen=True)
class Site:
    start: str
    target: str
    titles: dict[str, str]
    links: dict[str, tuple[str, ...]]  # page -> the pages it links to, in link order

    def page(self, page_id: str) -> tuple[str, ...]:
        if page_id not in self.links:
            raise ValueError(f"no page {page_id} on this site")
        return self.links[page_id]


class Draws:
    """A deterministic stream of choices from the seed: SHA-256 of the seed and a counter."""

    def __init__(self, seed: int) -> None:
        self.seed, self.count = seed, 0

    def below(self, bound: int) -> int:
        digest = hashlib.sha256(f"trap-mapper:{self.seed}:{self.count}".encode()).digest()
        self.count += 1
        return int.from_bytes(digest[:8], "big") % bound

    def pick(self, items):
        return items[self.below(len(items))]

    def shuffled(self, items):
        items = list(items)
        for index in range(len(items) - 1, 0, -1):
            other = self.below(index + 1)
            items[index], items[other] = items[other], items[index]
        return items


def build_site(seed: int) -> Site:
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be between 0 and {MAX_SEED}")
    draws = Draws(seed)
    core_count = 10 + draws.below(5)  # 10 to 14
    kinds = draws.shuffled(TRAP_KINDS)[: 2 + draws.below(3)]  # 2 to 4 trap clusters
    sizes = {"loop": 2, "ring": 3, "sink": 1, "funnel": 1}
    unreachable_count = 2 + draws.below(2)
    total = core_count + sum(sizes[kind] for kind in kinds) + (2 if "funnel" in kinds else 0) + unreachable_count
    ids = [START] + draws.shuffled(f"p{number:02d}" for number in range(1, total))
    core, rest = ids[:core_count], ids[core_count:]
    links: dict[str, list[str]] = {page: [] for page in ids}

    def link(source: str, target: str) -> None:
        if target not in links[source]:
            links[source].append(target)

    for here, there in pairwise(core):  # the core chain: start ... target
        link(here, there)
    for here in core:
        for _ in range(draws.below(3)):  # extra links within the core, any direction
            link(here, draws.pick(core))
    target = core[-1]

    traps: list[list[str]] = []
    for kind in kinds:
        cluster, rest = rest[: sizes[kind]], rest[sizes[kind]:]
        if kind == "loop":
            link(cluster[0], cluster[1])
            link(cluster[1], cluster[0])
        elif kind == "ring":
            for here, there in zip(cluster, cluster[1:] + cluster[:1], strict=True):
                link(here, there)
        traps.append(cluster)
    for index, kind in enumerate(kinds):
        if kind == "funnel":  # its links go only into a two-page loop of its own
            inner, rest = rest[:2], rest[2:]
            link(inner[0], inner[1])
            link(inner[1], inner[0])
            link(traps[index][0], inner[0])
            link(traps[index][0], inner[1])
    for cluster in traps:  # each trap is entered from a core page other than the target
        link(draws.pick(core[:-1]), cluster[0])

    # Keep the site shallow: while some page is more than MAX_DEPTH links from the start, the home page
    # links to the nearest core page on its way there. Core pages all reach the target, so the trap
    # pages stay exactly what they were.
    core_pages = set(core)
    while True:
        depth, parent = _layers(START, links)
        deepest = max(depth, key=lambda page: (depth[page], page))
        if depth[deepest] <= MAX_DEPTH:
            break
        page = deepest
        while page not in core_pages:
            page = parent[page]
        link(START, page)

    for page in rest:  # unreachable pages: they link into the core, nothing links to them
        link(page, draws.pick(core))

    names = draws.shuffled(TITLES)
    titles = dict(zip(ids, names, strict=False))
    titles[START] = "Home"
    titles[target] = "Goal: " + titles[target]
    return Site(START, target, titles, {page: tuple(found) for page, found in links.items()})


def trap_pages(site: Site) -> list[str]:
    """Pages reachable from the start from which the target cannot be reached, sorted."""
    reach = _reached(site.start, site.links)
    backward: dict[str, list[str]] = {page: [] for page in site.links}
    for page, found in site.links.items():
        for there in found:
            backward[there].append(page)
    return sorted(reach - _reached(site.target, backward))


def _layers(start: str, links) -> tuple[dict[str, int], dict[str, str]]:
    """Each reachable page's distance from ``start`` in links, and the page it was first reached from."""
    depth, parent, queue = {start: 0}, {}, deque([start])
    while queue:
        page = queue.popleft()
        for there in links[page]:
            if there not in depth:
                depth[there], parent[there] = depth[page] + 1, page
                queue.append(there)
    return depth, parent


def _reached(start: str, links) -> set[str]:
    seen, queue = {start}, deque([start])
    while queue:
        for there in links[queue.popleft()]:
            if there not in seen:
                seen.add(there)
                queue.append(there)
    return seen
