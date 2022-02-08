from hworkflow.project.base import Project


class ImageNet(Project):
    _parse_script = "$hanser/tools/parse_imagenet_log.py"
    # acc, acc5, loss, time
    _sheet_ranges = ["L", "M", "N", "O"]
    _update_methods = ["A", "A", "A", "W"]
    _commit_range = 'Q'
    _dep_repo = "hanser"
    _log_suffix1 = False

    def parse_log(self, log_file):
        result = super().parse_log(log_file)
        result = result[:-2] + [result[-2] + "\n\n" + result[-1]]
        return result