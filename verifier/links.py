"""list_links: the links of up to 20 pages."""

from .checks import MAX_PAGES, page_problem, result, seed_problem


def verify_input(value):
    problem = seed_problem(value.seed)
    if problem is None and not 1 <= len(value.page_ids) <= MAX_PAGES:
        problem = f"give 1 to {MAX_PAGES} page ids"
    if problem is None and len(set(value.page_ids)) != len(value.page_ids):
        problem = "a page id is given twice"
    for page in value.page_ids:
        problem = problem or page_problem(page)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    if [page.page_id for page in output_value.pages] != input_value.page_ids:
        return result(False, "the pages are not the ones asked for, in order")
    for page in output_value.pages:
        targets = [found.next_page_id for found in page.links]
        if len(set(targets)) != len(targets):
            return result(False, f"page {page.page_id} links to the same page twice")
        for target in targets:
            problem = page_problem(target)
            if problem:
                return result(False, problem)
        if not page.title.strip() or any(not found.label.strip() for found in page.links):
            return result(False, f"page {page.page_id} has a title and every link a label")
    return result(True, "links are well formed", pages=len(output_value.pages))
