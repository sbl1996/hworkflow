import sys
import time
import subprocess

from hhutil.io import fmt_path, read_text
from hworkflow.v2.callbacks import validate_callbacks


class Runner:

    def __init__(self, work_dir=None, retry_interval=30, **env_vars):
        super().__init__()
        if work_dir is None:
            work_dir = fmt_path("./")
        self.work_dir = work_dir
        self.retry_interval = retry_interval
        self.env_vars = env_vars
        self._python_exe = sys.executable

    def check_code(self, task_id):
        fp = self.work_dir / f"{task_id}.py"
        assert fp.exists(), "File not exists: {}".format(fp)

    def run_script(self, task_id, log_file):
        envs = {
            "TASK_ID": task_id,
            **self.env_vars,
        }
        python_exe = self._python_exe
        env_prefix = " ".join([f"{k}={v}" for k, v in envs.items()])
        fp = self.work_dir / f"{task_id}.py"
        cmd = f"{env_prefix} {python_exe} -u {fp} > {log_file} 2>&1"

        p = subprocess.run(cmd, shell=True)
        return p

    def run(self, task_id, log_file=None, max_retry=10, callbacks=()):
        self.check_code(task_id)
        validate_callbacks(callbacks, ['task_id', 'log_file'])

        if log_file is None:
            log_file = self.work_dir / f"{task_id}.log"
        else:
            log_file = fmt_path(log_file)

        retry = 0
        while True:
            p = self.run_script(task_id, log_file)
            if p.returncode == 0:
                self._context = {
                    'task_id': task_id,
                    'log_file': log_file,
                }
                for c in callbacks:
                    c.transform(self._context)
                print(f"{self._context['task_id']}-{self._context['sheet_seq']}")
            else:
                error_log = read_text(log_file)

                network_erros = [
                    "Socket closed",
                    "Connection reset by peer",
                ]

                functional_errors = [
                    "Stage end",
                    "Infinite encountered",
                ]
                # TODO: Connection timed out or CPU hang (usage 0%).
                #       The process will not return and block forever.
                possible_errors = network_erros + functional_errors

                if any(e in error_log for e in possible_errors):
                    retry += 1
                    if retry > max_retry:
                        raise RuntimeError("Failed to run task {} after {} retries".format(task_id, max_retry))
                    time.sleep(self.retry_interval)
                    continue
                else:
                    # Unknown error, left to user
                    print(error_log)
                    break