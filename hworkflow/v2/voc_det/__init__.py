from hhutil.io import read_text

from hworkflow.v2.callbacks import Callback, CleanLog, GetDependentRepoCommit, UpdateSheet, RenameLogWithSeq, \
    PushLogToGitHub
from hworkflow.v2.runner import Runner
from hworkflow.v2.parse import parse_log
from hworkflow.github import Github
from hworkflow.sheets import GoogleSheet


class ParseLog(Callback):

    def __init__(self):
        r"""
        Examples::
            >>> cb = ParseLog()
            >>> context = {'log_file': log_file}
            >>> cb.transform(context)
            >>> assert context['parse_result'] == ["80.67", "0.7896", "1:19:42\n189.8\n145.0"]
        """

    def requires(self):
        return ['log_file']

    def produces(self):
        return ['parse_result']

    def transform(self, context):
        log_file = context['log_file']
        result = parse_log(read_text(log_file), key='mAP', mode='max')
        result = result.split()
        result = result[:2] + [result[-3] + "\n" + result[-2] + "\n" + result[-1]]
        context['parse_result'] = result


class VOCDet(Runner):

    def __init__(self, name, git_repo, sheet_id, access_token, secret_file, token_file,
                 sub_sheet="Sheet1", worker_id=0, work_dir=None, retry_interval=30, **env_vars):
        env_vars = {**env_vars, "WORKER_ID": worker_id, "TASK_NAME": name}
        github = Github(git_repo, name, access_token)
        sheet = GoogleSheet(sheet_id, secret_file, token_file)

        sheet_ranges = ["N", "O", "P"]
        update_methods = ["A", "A", "W"]
        commit_range = 'R'
        dep_repo = "hanser"

        self._callbacks = [
            CleanLog(),
            ParseLog(),
            GetDependentRepoCommit(dep_repo),
            UpdateSheet(sheet, sheet_ranges, update_methods, commit_range, sub_sheet),
            RenameLogWithSeq(log_suffix1=False),
            PushLogToGitHub(github, retry_interval=retry_interval),
        ]

        super().__init__(work_dir, retry_interval, **env_vars)

    def run_retry(self, row, max_retry=10):
        self.run(row, log_file="train.log", max_retry=max_retry, callbacks=self._callbacks)
