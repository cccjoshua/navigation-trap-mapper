"""find-trap-pages: the agent's trap pages, compared with the traps computed on the reference graph.

Valid only when the set matches exactly: every trap reported, no page that can reach the target, no
page the start cannot reach, no page twice. The score is the Jaccard similarity of the two sets, so a
near miss shows how near it was.
"""

from .checks import page_problem, result, traps


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract TrapsOutput; ``reference``: the map_graph GraphOutput of the same seed."""
    if reference is None:
        return result(False, "no reference graph: the answer cannot be checked")
    reported = output.trap_pages
    for page in reported:
        problem = page_problem(page)
        if problem:
            return result(False, problem)
    if len(set(reported)) != len(reported):
        return result(False, "a page is reported twice")
    known = {page.page_id for page in reference.pages}
    unknown = sorted(set(reported) - known)
    if unknown:
        return result(False, f"the site has no page {', '.join(unknown)}", unknown=unknown)
    expected = traps(reference)
    given = set(reported)
    missing, extra = sorted(expected - given), sorted(given - expected)
    union = expected | given
    score = len(expected & given) / len(union) if union else 1.0
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missed {len(missing)} trap page(s)")
        if extra:
            parts.append(f"reported {len(extra)} page(s) that are not traps")
        return result(False, "; ".join(parts), score=score, missing=missing, extra=extra)
    return result(True, f"found all {len(expected)} trap pages", traps=len(expected))
