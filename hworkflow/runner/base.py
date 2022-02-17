import sys
import time
import subprocess
from itertools import dropwhile
from hhutil.io import read_lines, write_lines, read_text

ERRORS = [
    "Socket closed",
    "Connection reset by peer",
    "Stage end",
    "Infinite encountered",
]

class Runner:

    def __init__(self, **env_vars):
        super().__init__()
        self._env_vars = env_vars

        self._python_exe = sys.executable

    def run_script(self, name, log_file):
        envs = {
            "TASK_ID": name,
            **self._env_vars,
        }
        python_exe = self._python_exe
        env_prefix = " ".join([f"{k}={v}" for k, v in envs.items()])
        cmd = f"{env_prefix} {python_exe} -u {name}.py > {log_file} 2>&1"

        p = subprocess.run(cmd, shell=True)
        return p

    def run_retry(self, name, max_retry=10, skip_errors=None):
        retry = 0
        while retry <= max_retry:
            log_file = f"{name}.log"
            p = self.run_script(name, log_file)
            if p.returncode != 0:
                error_log = read_text(log_file)

                skip_errors = skip_errors or []
                possible_errors = ERRORS + list(skip_errors)
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
            break
