import sys
import time
import subprocess
from itertools import dropwhile
from typing import Tuple

from github import GithubException
from hhutil.io import fmt_path, read_lines, write_lines, read_text, eglob, rename

from hworkflow.github import Github
from hworkflow.sheets import GoogleSheet


class Project:

    _parse_script: str
    _sheet_range: Tuple[str, str]
    _sheet_update_last: bool = False
    _suffix1: bool = True

    def __init__(self, name, git_repo, sheet_id, access_token, secret_file, token_file, worker_id=0):
        super().__init__()
        self._name = name
        self._github = Github(git_repo, name, access_token)
        self._sheet = GoogleSheet(sheet_id, secret_file, token_file)
        self._worker_id = worker_id

        self._python_exe = sys.executable

    def fetch_code(self, row):
        content = self._github.fetch(f"code/{row}.py")
        fmt_path(f"{row}.py").write_text(content)

    def run_script(self, row, log_file):
        envs = {
            "WORKER_ID": self._worker_id,
            "TASK_NAME": self._name,
            "TASK_ID": row,
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
            f"{self._python_exe} {self._parse_script} -f {log_file}", shell=True).decode().split()
        return result

    def get_log_name(self, row, seq):
        name = f"{row}" if seq == 1 and not self._suffix1 else f"{row}-{seq}"
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
        new_result = self.parse_log(log_file)
        seq = self._sheet.append_result(
            row, self._sheet_range, new_result, self._sheet_update_last)

        log_name = self.get_log_name(row, seq)
        print(log_name)
        self.push_log(log_name, read_text(log_file))
        rename(log_file, log_name)
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

            seq = self.sync_result(row, log_file)
            if seq >= max_repeat:
                break

    def run_retry(self, row, max_retry=10):
        self.check_code(row)

        retry = 0
        log_files = []
        while retry <= max_retry:
            log_file = f"train#{retry}.log"
            p = self.run_script(row, log_file)
            log_files.append(log_file)
            if p.returncode != 0:
                error_log = read_text(log_file)

                # Network error, resolve by retry
                possible_errors = [
                    "Socket closed",
                    "Connection reset by peer",
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
            previous_log = fmt_path("train#p.log")
            if previous_log.exists():
                log_files.insert(0, previous_log)
            # Merge all log files include previous ones produced by runs with error
            lines = merge_log_files(log_files)
            log_file = f"{row}#m.log"
            write_lines(lines, log_file)

            self.sync_result(row, log_file)
            break


def merge_log_files(log_files):
    all_lines = []
    for log_file in log_files:
        lines = read_lines(log_file)

        # Error messages are dropped for debugging
        drop_prefixes = [
            "WARNING",
            "Instructions for updating",
            "Use",
        ]
        lines = filter(lambda l: not any(l.startswith(s) for s in drop_prefixes),
                       dropwhile(lambda l: 'Start training' not in l, lines))
        new_lines = []
        is_error_msg = False
        for l in lines:
            if not is_error_msg and l.startswith("Traceback"):
                is_error_msg = True
            if is_error_msg and l.endswith("Start training"):
                is_error_msg = False
            if not is_error_msg:
                new_lines.append(l)
        lines = new_lines
        all_lines.extend(lines)
    return all_lines
