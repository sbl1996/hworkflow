from hhutil.io import read_text

from hworkflow.v2.callbacks import Callback, CleanLog, GetDependentRepoCommit, UpdateSheet, RenameLogWithSeq, PushLogToGitHub
from hworkflow.v2.runner import Runner
from hworkflow.v2.imagenet.parse import parse_imagenet_log
from hworkflow.github import Github
from hworkflow.sheets import GoogleSheet


class ParseImageNetLog(Callback):

    def __init__(self):
        r"""
        Examples::
            >>> cb = ParseImageNetLog()
            >>> context = {'log_file': log_file}
            >>> cb.transform(context)
            >>> assert context['parse_result'] == ["77.24", "93.46", "1.9508", "21:39:46\n\n324.5"]
        """

    def requires(self):
        return ['log_file']

    def produces(self):
        return ['parse_result']

    def transform(self, context):
        log_file = context['log_file']
        result = parse_imagenet_log(read_text(log_file))
        result = [f.format(r) for f, r in zip(["%.2f", "%.2f", ".4f", "%s", "%.1f"], result)]
        result = result[:-2] + [result[-2] + "\n\n" + result[-1]]
        context['parse_result'] = result


class ImageNet(Runner):

    def __init__(self, name, git_repo, sheet_id, access_token, secret_file, token_file, worker_id=0,
                 work_dir=None, retry_interval=30, **env_vars):
        env_vars = {**env_vars, "WORKER_ID": worker_id, "TASK_NAME": name}
        github = Github(git_repo, name, access_token)
        sheet = GoogleSheet(sheet_id, secret_file, token_file)

        sheet_ranges = ["L", "M", "N", "O"]
        update_methods = ["A", "A", "A", "W"]
        commit_range = 'Q'
        dep_repo = "hanser"

        self._callbacks = [
            CleanLog(),
            ParseImageNetLog(),
            GetDependentRepoCommit(dep_repo),
            UpdateSheet(sheet, sheet_ranges, update_methods, commit_range),
            RenameLogWithSeq(suffix1=False),
            PushLogToGitHub(github, retry_interval=retry_interval),
        ]

        super().__init__(work_dir, retry_interval, **env_vars)

    def run_retry(self, row, max_retry=10):
        self.run(row, log_file="train.log", max_retry=max_retry, callbacks=self._callbacks)
