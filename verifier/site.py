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
    return result(True, "site is well formed")
