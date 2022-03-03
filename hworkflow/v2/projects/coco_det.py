from hworkflow.v2.project import Project
from hworkflow.v2.parse import parse_log


def parse_fn(content):
    r"""
    Examples::
        >>> parse_fn(content)
        >>> ["45.47", "1.3986", "9:10:14\n1362.0\n1271.6"]
    """
    result = parse_log(content, key='AP', mode='final')
    result = result.split()
    result = result[:2] + [result[-3] + "\n" + result[-2] + "\n" + result[-1]]
    return result


class COCODet(Project):
    parse_fn = parse_fn
    sheet_ranges = ["N", "O", "P"]
    update_methods = ["A", "A", "W"]
    commit_range = 'R'
    dep_repo = "hanser"
    log_suffix1 = False