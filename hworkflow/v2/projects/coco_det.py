from hworkflow.v2.project import Project
from hworkflow.v2.parse import parse_log


class COCODet(Project):
    sheet_ranges = ["N", "O", "P"]
    update_methods = ["A", "A", "W"]
    commit_range = 'R'
    dep_repo = "hanser"

    def parse_log(self, content):
        r"""
        Examples::
            >>> self.parse_log(content)
            >>> ["45.47", "1.3986", "9:10:14\n1362.0\n1271.6"]
        """
        result = parse_log(content, key='AP', mode='max')
        result = result.split()
        result = result[:2] + [result[-3] + "\n" + result[-2] + "\n" + result[-1]]
        return result