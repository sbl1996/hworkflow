from hworkflow.v2.project import Project
from hworkflow.v2.parse import parse_log


class Cityscapes(Project):
    sheet_ranges = ["M", "N", "O"]
    update_methods = ["A", "A", "W"]
    commit_range = 'Q'
    dep_repo = "hanser"

    def parse_log(self, content):
        r"""
        Examples::
            >>> self.parse_log(content)
            >>> ["78.85(79.01)", "0.1104(0.1111)", "10:21:52\n308.4\n284.9"]
        """
        result = parse_log(content, key='miou', mode='all')
        result = result.split()
        result = result[:2] + [result[-3] + "\n" + result[-2] + "\n" + result[-1]]
        return result