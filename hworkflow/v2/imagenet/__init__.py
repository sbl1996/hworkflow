from hworkflow.v2.project import Project
from hworkflow.v2.imagenet.parse import parse_imagenet_log


def parse_fn(content):
    r"""
    Examples::
        >>> parse_fn(content)
        >>> ["77.24", "93.46", "1.9508", "21:39:46\n\n324.5"]
    """
    result = parse_imagenet_log(content)
    result = [f.format(r) for f, r in zip(["%.2f", "%.2f", ".4f", "%s", "%.1f"], result)]
    result = result[:-2] + [result[-2] + "\n\n" + result[-1]]
    return result


class ImageNet(Project):
    parse_fn = parse_fn
    sheet_ranges = ["L", "M", "N", "O"]
    update_methods = ["A", "A", "A", "W"]
    commit_range = 'Q'
    log_suffix1 = False
    dep_repo = "hanser"
