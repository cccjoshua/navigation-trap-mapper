"""The plugin's tools: each takes its contract input and the workspace, and reads the seed's site."""

from __future__ import annotations

from pathlib import Path

from contract import GraphOutput, GraphPage, Link, LinksOutput, PageInput, PageLinks, SeedInput, SiteOutput
from plugin.site import MAX_PAGES, build_site, trap_pages


def start_site(given: SeedInput, workspace: Path) -> SiteOutput:
    site = build_site(given.seed)
    return SiteOutput(seed=given.seed, start_page_id=site.start, target_page_id=site.target)


def list_links(given: PageInput, workspace: Path) -> LinksOutput:
    if not 1 <= len(given.page_ids) <= MAX_PAGES or len(set(given.page_ids)) != len(given.page_ids):
        raise ValueError(f"give 1 to {MAX_PAGES} distinct page ids")
    site = build_site(given.seed)
    for page in given.page_ids:
        site.page(page)  # raises for a page the site does not have
    return LinksOutput(
        pages=[
            PageLinks(
                page_id=page,
                title=site.titles[page],
                links=[Link(label=f"Open {site.titles[there]}", next_page_id=there) for there in site.page(page)],
            )
            for page in given.page_ids
        ]
    )


def map_graph(given: SeedInput, workspace: Path) -> GraphOutput:
    """The reference: the whole link graph, run out of the agent's sight."""
    site = build_site(given.seed)
    return GraphOutput(
        start_page_id=site.start,
        target_page_id=site.target,
        pages=[GraphPage(page_id=page, links=list(found)) for page, found in sorted(site.links.items())],
        trap_pages=trap_pages(site),
    )
