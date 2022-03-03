from hworkflow.v2.project import Project
from hworkflow.v2.parse import parse_log


class VOCSeg(Project):
    sheet_ranges = ["L", "M", "N"]
    update_methods = ["A", "A", "W"]
    commit_range = 'P'
    dep_repo = "hanser"

    def parse_log(self, content):
        r"""
        Examples::
            >>> self.parse_log(content)
            >>> ["77.63(77.98)", "0.0772(0.0792)", "1:09:03\n67.2\n60.0"]
        """
        result = parse_log(content, key='miou', mode='all')
        result = result.split()
        result = result[:2] + [result[-3] + "\n" + result[-2] + "\n" + result[-1]]
        return result