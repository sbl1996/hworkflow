from hworkflow.v2.project import Project
from hworkflow.v2.parse import parse_log


class VOCDet(Project):
    sheet_ranges = ["N", "O", "P"]
    update_methods = ["A", "A", "W"]
    commit_range = 'R'
    dep_repo = "hanser"
    log_suffix1 = False

    def parse_log(self, content):
        r"""
        Examples::
            >>> self.parse_log(content)
            >>> ["80.67", "0.7896", "1:19:42\n189.8\n145.0"]
        """
        result = parse_log(content, key='mAP', mode='max')
        result = result.split()
        result = result[:2] + [result[-3] + "\n" + result[-2] + "\n" + result[-1]]
        return result