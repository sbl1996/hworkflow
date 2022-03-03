from hhutil.io import read_text

from hworkflow.v2.callbacks import Callback, CleanLog, GetDependentRepoCommit, UpdateSheet, RenameLogWithSeq, \
    PushLogToGitHub
from hworkflow.v2.runner import Runner
from hworkflow.v2.parse import parse_log
from hworkflow.github import Github
from hworkflow.sheets import GoogleSheet


class ParseCIFARLog(Callback):

    def __init__(self):
        r"""
        Examples::
            >>> cb = ParseCIFARLog()
            >>> context = {'log_file': log_file}
            >>> cb.transform(context)
            >>> assert context['parse_result'] == ["80.13(80.38)", "0.0125(0.0146)", "4.9"]
        """

    def requires(self):
        return ['log_file']

    def produces(self):
        return ['parse_result']

    def transform(self, context):
        log_file = context['log_file']
        result = parse_log(read_text(log_file))
        result = result.split()
        result = [result[0], result[1], result[3]]
        context['parse_result'] = result


class CIFAR(Runner):

    def __init__(self, name, git_repo, sheet_id, access_token, secret_file, token_file, worker_id=0,
                 work_dir=None, retry_interval=30, **env_vars):
        env_vars = {**env_vars, "WORKER_ID": worker_id, "TASK_NAME": name}
        github = Github(git_repo, name, access_token)
        sheet = GoogleSheet(sheet_id, secret_file, token_file)

        sheet_ranges = ["K", "L", "M"]
        update_methods = ["A", "A", "W"]
        commit_range = 'O'
        dep_repo = "hanser"

        self._callbacks = [
            CleanLog(),
            ParseCIFARLog(),
            GetDependentRepoCommit(dep_repo),
            UpdateSheet(sheet, sheet_ranges, update_methods, commit_range),
            RenameLogWithSeq(suffix1=True),
            PushLogToGitHub(github, retry_interval=retry_interval),
        ]

        super().__init__(work_dir, retry_interval, **env_vars)

    def run_retry(self, row, max_retry=10):
        self.run(row, log_file="train.log", max_retry=max_retry, callbacks=self._callbacks)
