"""map_graph, the reference: the whole link graph."""

from .checks import START, result, seed_problem, traps


def verify_input(value):
    problem = seed_problem(value.seed)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    ids = [page.page_id for page in output_value.pages]
    known = set(ids)
    if len(known) != len(ids):
        return result(False, "the graph lists a page twice")
    if output_value.start_page_id != START or output_value.target_page_id not in known:
        return result(False, f"the graph starts on {START} and its target is one of its pages")
    if any(there not in known for page in output_value.pages for there in page.links):
        return result(False, "a page links to a page the graph does not have")
    expected = sorted(traps(output_value))
    if output_value.trap_pages != expected:
        return result(False, "trap_pages is not what the graph gives", expected=expected)
    return result(True, "graph is consistent", pages=len(ids), traps=len(expected))
