"""start_site: the start and target pages."""

from .checks import START, page_problem, result, seed_problem


def verify_input(value):
    problem = seed_problem(value.seed)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    if output_value.seed != input_value.seed:
        return result(False, "the site is for another seed")
    if output_value.start_page_id != START:
        return result(False, f"a site starts on {START}")
    problem = page_problem(output_value.target_page_id)
    if problem or output_value.target_page_id == START:
        return result(False, problem or "the target is not the start page")
    count = output_value.page_count
    if not 2 <= count <= 100 or int(output_value.target_page_id[1:]) >= count:
        return result(False, "the page count does not cover the start and target pages")
    return result(True, "site is well formed")
