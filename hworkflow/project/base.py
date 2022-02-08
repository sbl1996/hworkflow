import sys
import time
import subprocess
from itertools import dropwhile
from typing import List, Optional
import pkg_resources

from github import GithubException
from hhutil.io import fmt_path, read_lines, write_lines, read_text, rename, copy

from hworkflow.github import Github
from hworkflow.sheets import GoogleSheet
from hworkflow.utils import retry_fn


class Project:

    _parse_script: str
    _sheet_ranges: List[str]
    _update_methods: List[str]
    _log_suffix1: bool = True
    _commit_range: Optional[str] = None
    _dep_repo: Optional[str] = None

    def __init__(self, name, git_repo, sheet_id, access_token, secret_file, token_file, worker_id=0, **env_vars):
        super().__init__()
        assert len(self._sheet_ranges) == len(self._update_methods)
        self._parse_script_path = self._parse_script
        if self._commit_range is not None:
            assert self._dep_repo is not None
        if self._dep_repo is not None:
            self._dep_repo_path = pkg_resources.get_distribution(self._dep_repo).module_path
            if self._parse_script.startswith("$" + self._dep_repo):
                self._parse_script_path = self._parse_script.replace(
                    "$" + self._dep_repo, self._dep_repo_path)
        self._name = name
        self._github = Github(git_repo, name, access_token)
        self._sheet = GoogleSheet(sheet_id, secret_file, token_file)
        self._worker_id = worker_id
        self._env_vars = env_vars

        self._python_exe = sys.executable

    def _get_repo_commit(self):
        fp = fmt_path(self._dep_repo_path)
        return subprocess.check_output(
            f'cd {fp} && git log --format="%h" -n 1', shell=True).decode().strip()

    def fetch_code(self, row):
        content = self._github.fetch(f"code/{row}.py")
        fmt_path(f"{row}.py").write_text(content)

    def run_script(self, row, log_file):
        envs = {
            "WORKER_ID": self._worker_id,
            "TASK_NAME": self._name,
            "TASK_ID": row,
            **self._env_vars,
        }
        python_exe = self._python_exe
        env_prefix = " ".join([f"{k}={v}" for k, v in envs.items()])
        cmd = f"{env_prefix} {python_exe} -u {row}.py > {log_file} 2>&1"

        p = subprocess.run(cmd, shell=True)
        return p

    def check_code(self, row):
        assert fmt_path(f"{row}.py").exists(), "Fetch code and check it first."

    def parse_log(self, log_file):
        result = subprocess.check_output(
            f"{self._python_exe} {self._parse_script_path} -f {log_file}", shell=True).decode().split()
        return result

    def get_log_name(self, row, seq):
        name = f"{row}" if seq == 1 and not self._log_suffix1 else f"{row}-{seq}"
        return name

    def push_log(self, log_name, content, max_retry=3):
        path = "log/" + log_name + ".log"
        try:
            self._github.push(path, content)
        except GithubException as e:
            if max_retry > 0:
                time.sleep(10)
                self.push_log(log_name, content, max_retry - 1)
            else:
                raise e

    def sync_result(self, row, log_file):
        try:
            new_result = self.parse_log(log_file)
        except subprocess.CalledProcessError:
            print(read_text(log_file))
            raise ValueError("Log file parse error.")
        ranges = self._sheet_ranges
        update_methods = self._update_methods
        if self._commit_range is not None:
            ranges = [*ranges, self._commit_range]
            new_result.append(self._get_repo_commit())
            update_methods = [*update_methods, 'A']
        seq = self._sheet.append_result(
            row, ranges, new_result, update_methods)

        log_name = self.get_log_name(row, seq)
        print(log_name)
        self.push_log(log_name, read_text(log_file))
        log_file = fmt_path(log_file)
        copy(log_file, log_file.with_name(log_name + log_file.suffix))
        return seq

    def run_repeat(self, row, max_repeat=5):
        self.check_code(row)

        while True:
            log_file = "train.log"
            p = self.run_script(row, log_file)
            if p.returncode != 0:
                # Runtime error, left to user
                print(read_text(log_file))
                break

            lines = read_lines(log_file)
            lines = list(dropwhile(lambda l: 'Start training' not in l, lines))
            write_lines(lines, log_file)

            seq = retry_fn(lambda: self.sync_result(row, log_file), 3,
                           catch=(BrokenPipeError,), interval=10)
            # seq = self.sync_result(row, log_file)

            if seq >= max_repeat:
                break


    def run_retry(self, row, max_retry=10):
        self.check_code(row)

        retry = 0
        while retry <= max_retry:
            log_file = f"train.log"
            p = self.run_script(row, log_file)
            if p.returncode != 0:
                error_log = read_text(log_file)

                # Network error, resolve by retry
                possible_errors = [
                    "Socket closed",
                    "Connection reset by peer",
                    "Stage end"
                ]
                # TODO: Connection timed out. The process will not return and block forever.
                if any(e in error_log for e in possible_errors):
                    retry += 1
                    time.sleep(30)
                    continue
                else:
                    # Unknown error, left to user
                    print(error_log)
                    break

            lines = read_lines(log_file)
            lines = list(dropwhile(lambda l: 'Start training' not in l, lines))
            write_lines(lines, log_file)

            retry_fn(lambda: self.sync_result(row, log_file), 3,
                     catch=(BrokenPipeError,), interval=10)
            break

    def run_retry2(self, row, max_retry=10):
        self.run_retry(row, max_retry)
