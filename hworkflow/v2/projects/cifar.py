from hworkflow.v2.project import Project
from hworkflow.v2.parse import parse_log


class CIFAR(Project):
    sheet_ranges = ["K", "L", "M"]
    update_methods = ["A", "A", "W"]
    commit_range = 'O'
    dep_repo = "hanser"
    log_suffix1 = True

    def parse_log(self, content):
        r"""
        Examples::
            >>> self.parse_log(content)
            >>> ["80.13(80.38)", "0.0125(0.0146)", "4.9"]
        """
        result = parse_log(content)
        result = result.split()
        result = [result[0], result[1], result[3]]
        return result
