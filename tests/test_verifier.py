from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, GraphOutput, PageInput, SeedInput, Task, Tool
from plugin import list_links, map_graph, start_site
from plugin.site import build_site, trap_pages

TASK = "find-trap-pages"
SEEDS = range(60)


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_task(seed: int, pages: list[str], reference: GraphOutput | None, workspace: Path) -> dict:
    given, made = TASKS[Task(TASK)]
    pinned = None if reference is None else build_output(plain_output(reference), GraphOutput)
    output = build_output({"trap_pages": pages}, made)
    return verifier.verify_task(TASK, build_output({"seed": seed}, given), output, pinned, str(workspace))


def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, given: dict, made: dict) -> dict:
    given_class, made_class = TOOLS[Tool(tool)]
    return verifier.verify_output(tool, build_output(given, given_class), build_output(made, made_class), "")


def graph(seed: int) -> GraphOutput:
    return map_graph(SeedInput(seed=seed), None)


# Correct


@pytest.mark.parametrize("seed", SEEDS)
def test_approves_exactly_the_trap_pages_in_any_order(seed: int, tmp_path: Path) -> None:
    traps = trap_pages(build_site(seed))
    assert verify_task(seed, traps, graph(seed), tmp_path)["valid"] is True
    verdict = verify_task(seed, traps[::-1], graph(seed), tmp_path)
    assert verdict["valid"] is True and verdict["score"] == 1.0


# Incorrect


@pytest.mark.parametrize("seed", SEEDS)
def test_refuses_a_missed_trap_with_a_partial_score(seed: int, tmp_path: Path) -> None:
    traps = trap_pages(build_site(seed))
    verdict = verify_task(seed, traps[1:], graph(seed), tmp_path)
    assert verdict["valid"] is False and "missed 1" in verdict["message"]
    assert verdict["details"]["missing"] == traps[:1]
    assert verdict["score"] == pytest.approx((len(traps) - 1) / len(traps))


@pytest.mark.parametrize("seed", SEEDS)
def test_refuses_pages_that_are_not_traps(seed: int, tmp_path: Path) -> None:
    site = build_site(seed)
    traps = trap_pages(site)
    for wrong in (site.target, site.start):
        verdict = verify_task(seed, traps + [wrong], graph(seed), tmp_path)
        assert verdict["valid"] is False and verdict["details"]["extra"] == [wrong]
    unreachable = sorted(set(site.links) - set(traps) - {
        page for page in site.links if page in _reachable(site)})
    verdict = verify_task(seed, traps + unreachable[:1], graph(seed), tmp_path)
    assert verdict["valid"] is False and "not traps" in verdict["message"]


def _reachable(site) -> set[str]:
    seen, stack = {site.start}, [site.start]
    while stack:
        for there in site.links[stack.pop()]:
            if there not in seen:
                seen.add(there)
                stack.append(there)
    return seen


def test_refuses_a_repeated_or_unknown_page(tmp_path: Path) -> None:
    traps = trap_pages(build_site(7))
    verdict = verify_task(7, traps + traps[:1], graph(7), tmp_path)
    assert verdict["valid"] is False and "twice" in verdict["message"]
    verdict = verify_task(7, traps + ["p99"], graph(7), tmp_path)
    assert verdict["valid"] is False and "no page p99" in verdict["message"]
    verdict = verify_task(7, traps + ["home"], graph(7), tmp_path)
    assert verdict["valid"] is False and "not a page id" in verdict["message"]


def test_refuses_another_seeds_traps(tmp_path: Path) -> None:
    other = next(seed for seed in range(1, 50) if trap_pages(build_site(seed)) != trap_pages(build_site(0)))
    assert verify_task(0, trap_pages(build_site(other)), graph(0), tmp_path)["valid"] is False


# Missing


def test_refuses_an_empty_answer_or_a_missing_reference(tmp_path: Path) -> None:
    verdict = verify_task(7, [], graph(7), tmp_path)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    verdict = verify_task(7, trap_pages(build_site(7)), None, tmp_path)
    assert verdict["valid"] is False and "no reference" in verdict["message"]


# Malformed: the contract refuses a value of the wrong shape before the verifier sees it.


@pytest.mark.parametrize("output", [{}, {"trap_pages": "p01,p02"}, {"trap_pages": [1, 2]}, {"pages": ["p01"]}])
def test_the_contract_refuses_a_malformed_answer(output: dict) -> None:
    with pytest.raises(Exception):  # noqa: B017 - slimconfig's error type is its own
        build_output(output, TASKS[Task(TASK)][1])


def test_refuses_malformed_tool_input() -> None:
    assert verify_input("list_links", {"seed": 7, "page_ids": ["p03", "p04"]})["valid"] is True
    assert verify_input("list_links", {"seed": 7, "page_ids": ["home"]})["valid"] is False
    assert verify_input("list_links", {"seed": 7, "page_ids": []})["valid"] is False
    assert verify_input("list_links", {"seed": 7, "page_ids": ["p03", "p03"]})["valid"] is False
    assert verify_input("list_links", {"seed": 7, "page_ids": [f"p{n:02d}" for n in range(41)]})["valid"] is False
    assert verify_input("start_site", {"seed": -5})["valid"] is False
    assert verify_input("map_graph", {"seed": 1_000_001})["valid"] is False


# Boundary


def test_boundary_seeds_build_valid_sites(tmp_path: Path) -> None:
    for seed in (0, 1_000_000):
        traps = trap_pages(build_site(seed))
        assert verify_task(seed, traps, graph(seed), tmp_path)["valid"] is True


def test_a_graph_with_no_traps_takes_an_empty_answer(tmp_path: Path) -> None:
    found = plain_output(graph(7))
    kept = {found["start_page_id"], found["target_page_id"]}
    found["pages"] = [
        {"page_id": found["start_page_id"], "links": [found["target_page_id"]]},
        {"page_id": found["target_page_id"], "links": [found["start_page_id"]]},
    ]
    found["trap_pages"] = []
    assert {page["page_id"] for page in found["pages"]} == kept
    reference = build_output(found, GraphOutput)
    assert verify_task(7, [], reference, tmp_path)["valid"] is True
    assert verify_output("map_graph", {"seed": 7}, found)["valid"] is True


# Each tool's own checks


def test_tool_outputs_pass_their_checks_and_tampered_ones_do_not() -> None:
    site = plain_output(start_site(SeedInput(seed=7), None))
    assert verify_output("start_site", {"seed": 7}, site)["valid"] is True
    assert verify_output("start_site", {"seed": 8}, site)["valid"] is False

    asked = {"seed": 7, "page_ids": ["p00", "p01"]}
    links = plain_output(list_links(PageInput(**asked), None))
    assert verify_output("list_links", asked, links)["valid"] is True
    assert verify_output("list_links", {"seed": 7, "page_ids": ["p01", "p00"]}, links)["valid"] is False
    first = links["pages"][0]
    doubled = {"pages": [first | {"links": first["links"] + first["links"][:1]}, links["pages"][1]]}
    assert verify_output("list_links", asked, doubled)["valid"] is False

    found = plain_output(graph(7))
    assert verify_output("map_graph", {"seed": 7}, found)["valid"] is True
    lied = found | {"trap_pages": found["trap_pages"][1:]}
    assert verify_output("map_graph", {"seed": 7}, lied)["valid"] is False


def test_the_verdict_is_the_same_every_time(tmp_path: Path) -> None:
    traps = trap_pages(build_site(11))[1:]
    verdicts = [verify_task(11, traps, graph(11), tmp_path) for _ in range(3)]
    assert verdicts[0] == verdicts[1] == verdicts[2]
