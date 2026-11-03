"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    START_SITE = "start_site"
    LIST_LINKS = "list_links"
    MAP_GRAPH = "map_graph"


class Task(Enum):
    FIND_TRAP_PAGES = "find-trap-pages"


SEED = "The site's seed, 0 to 1000000: the same seed always builds the same site"
PAGE_ID = "A page id, p followed by two digits, e.g. p00"


@dataclass
class SeedInput(Output):
    seed: Annotated[int, SEED]


@dataclass
class SiteOutput(Output):
    seed: Annotated[int, SEED]
    start_page_id: Annotated[str, "The page exploration starts on"]
    target_page_id: Annotated[str, "The page every route should be able to reach"]
    page_count: Annotated[int, "How many pages the site has: they are p00, p01, ... up to the last one, p followed by page_count minus 1"]


@dataclass
class PageInput(Output):
    seed: Annotated[int, SEED]
    page_ids: Annotated[list[str], "The pages to list, 1 to 40 distinct page ids, e.g. [p00, p07]"]


@dataclass
class Link(Output):
    label: Annotated[str, "The link's text"]
    next_page_id: Annotated[str, "The page the link leads to"]


@dataclass
class PageLinks(Output):
    page_id: Annotated[str, PAGE_ID]
    title: Annotated[str, "The page's title"]
    links: Annotated[list[Link], "Every link on the page; empty when the page has none"]


@dataclass
class LinksOutput(Output):
    pages: Annotated[list[PageLinks], "Each page asked for, in the order given"]


@dataclass
class GraphPage(Output):
    page_id: Annotated[str, PAGE_ID]
    links: Annotated[list[str], "The pages this page links to, in its link order"]


@dataclass
class GraphOutput(Output):
    start_page_id: Annotated[str, "The start page"]
    target_page_id: Annotated[str, "The target page"]
    pages: Annotated[list[GraphPage], "Every page of the site, reachable or not"]
    trap_pages: Annotated[list[str], "Pages reachable from the start that cannot reach the target, sorted"]


@dataclass
class TrapsOutput(Output):
    trap_pages: Annotated[
        list[str], "Every page reachable from the start page from which the target can never be reached"
    ]


TOOLS = {
    Tool.START_SITE: (SeedInput, SiteOutput),
    Tool.LIST_LINKS: (PageInput, LinksOutput),
    Tool.MAP_GRAPH: (SeedInput, GraphOutput),
}
TASKS = {
    Task.FIND_TRAP_PAGES: (SeedInput, TrapsOutput),
}
