from typing import List, Optional, Callable
from hworkflow.v2.callbacks import CleanLog, ParseLog, GetDependentRepoCommit, UpdateSheet, RenameLogWithSeq, PushLogToGitHub
from hworkflow.v2.runner import Runner
from hworkflow.github import Github
from hworkflow.sheets import GoogleSheet


class Project:

    parse_fn: Callable[[str], List[str]]
    sheet_ranges: List[str]
    update_methods: List[str]
    log_suffix1: bool = True
    commit_range: Optional[str] = None
    dep_repo: str

    def __init__(self, name, git_repo, sheet_id, access_token, secret_file, token_file,
                 sub_sheet="Sheet1", worker_id=0, work_dir=None, retry_interval=30, **env_vars):
        self.github = Github(git_repo, name, access_token)
        self.sheet = GoogleSheet(sheet_id, secret_file, token_file)

        env_vars = {**env_vars, "WORKER_ID": worker_id, "TASK_NAME": name}
        self.runner = Runner(work_dir, retry_interval, env_vars)

        self._callbacks = [
            CleanLog(),
            ParseLog(self.parse_fn),
            GetDependentRepoCommit(self.dep_repo),
            UpdateSheet(self.sheet, self.sheet_ranges, self.update_methods, self.commit_range, sub_sheet),
            RenameLogWithSeq(suffix1=self.log_suffix1),
            PushLogToGitHub(self.github, retry_interval=retry_interval),
        ]

        super().__init__(work_dir, retry_interval, **env_vars)

    def run_retry(self, row, max_retry=10):
        self.runner.run(row, log_file="train.log", max_retry=max_retry, callbacks=self._callbacks)

    def fetch_code(self, row):
        content = self.github.fetch(f"code/{row}.py")
        (self.runner.work_dir / f"{row}.py").write_text(content)
