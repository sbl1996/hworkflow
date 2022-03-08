import sys
import time
import subprocess

from hhutil.io import fmt_path, read_text, time_now
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
        cmd = f"{env_prefix} exec {python_exe} -u {fp} > {log_file} 2>&1"

        p = subprocess.Popen(cmd, shell=True)
        return p

    def run(self, task_id, log_file=None, max_retry=10, callbacks=(), log_timeout=None):
        self.check_code(task_id)
        validate_callbacks(callbacks, ['task_id', 'log_file'])

        if log_file is None:
            log_file = self.work_dir / f"{task_id}.log"
        else:
            log_file = fmt_path(log_file)

        retry = 0
        while True:
            is_sleeping = False
            proc = self.run_script(task_id, log_file)
            poll_count = 0
            try:
                poll_interval = 10
                mtime = None
                while proc.poll() is None:
                    time.sleep(poll_interval)
                    poll_count += 1
                    if poll_count * poll_interval < log_timeout:
                        continue
                    if mtime is None:
                        mtime = log_file.stat().st_mtime
                    last_mtime = mtime
                    mtime = log_file.stat().st_mtime
                    if log_timeout is not None and mtime - last_mtime > log_timeout:
                        print(f"{time_now()} Detect sleeping, kill it")
                        proc.kill()
                        is_sleeping = True
                        break
            except KeyboardInterrupt as e:
                proc.kill()
                raise e
            except Exception as e:
                proc.kill()
                print(e)
                exit(1)

            if proc.returncode != 0:
                if is_sleeping:
                    retry += 1
                    if retry > max_retry:
                        raise RuntimeError("Failed to run task {} after {} retries".format(task_id, max_retry))
                    time.sleep(self.retry_interval)
                    continue
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
                    # TODO: Connection timed out. The process will not return and block forever.
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
            else:
                self._context = {
                    'task_id': task_id,
                    'log_file': log_file,
                }
                for c in callbacks:
                    c.transform(self._context)
                print(f"{self._context['task_id']}-{self._context['sheet_seq']}")
                break
