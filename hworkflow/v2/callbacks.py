import pkg_resources
import subprocess

from itertools import dropwhile

from github import GithubException

from hhutil.io import read_lines, write_lines, fmt_path, copy, read_text
from hworkflow.utils import retry_fn


class Callback:

    def requires(self):
        return []

    def produces(self):
        return []

    def transform(self, context):
        # default context
        # {task_id, log_file}
        raise NotImplemented


def validate_callbacks(callbacks, initial_context_keys):
    context_keys = set(initial_context_keys)
    for callback in callbacks:
        for key in callback.requires():
            assert key in context_keys, f"{key} not found in context"
        for key in callback.produces():
            context_keys.add(key)


class CleanLog(Callback):

    def requires(self):
        return ['log_file']

    def transform(self, context):
        log_file = context['log_file']
        lines = read_lines(log_file)
        lines = list(dropwhile(lambda l: 'Start training' not in l, lines))
        write_lines(lines, log_file)


class GetDependentRepoCommit(Callback):

    def __init__(self, dep_repo):
        r"""
        Examples::
            >>> cb = GetDependentRepoCommit('hanser')
            >>> cb.transform(context)
            >>> assert context['repo_commit'] == 'f9f9f9'
        """
        self.dep_repo = dep_repo
        repo_path =  pkg_resources.get_distribution(self.dep_repo).module_path
        repo_path = fmt_path(repo_path)
        assert repo_path.exists(), f"{repo_path} not found"
        self.repo_path = repo_path

    def produces(self):
        return ['repo_commit']

    def transform(self, context):
        commit = subprocess.check_output(
            f'cd {self.repo_path} && git log --format="%h" -n 1', shell=True).decode().strip()
        context['repo_commit'] = commit


class UpdateSheet(Callback):

    def __init__(self, sheet, sheet_ranges, update_methods, commit_range=None, sub_sheet='Sheet1'):
        r"""
        Examples::
            >>> sheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
            >>> secret_file = "credentials.json"
            >>> token_file = "token.pickle"
            >>> sheet = GoogleSheet(sheet_id, secret_file, token_file)
            >>> sheet_ranges = ["L", "M", "N", "O"]
            >>> update_methods = ["A", "A", "A", "W"]
            >>> commit_range = "Q"
            >>> cb = UpdateSheet(sheet, sheet_ranges, update_methods, commit_range)
            >>> context = {'parse_result': ["77.24", "93.46", "1.9508", "21:39:46\n\n324.5"],
            >>>            'task_id': "463", 'repo_commit': "f9b8f8e"}
            >>> cb.transform(context)
            >>> assert context['sheet_seq'] == 1
        """

        self.sheet = sheet
        self.sheet_ranges = sheet_ranges
        self.update_methods = update_methods
        self.commit_range = commit_range
        self.sub_sheet = sub_sheet

    def requires(self):
        r = ['task_id', 'parse_result']
        if self.commit_range is not None:
            r.append('repo_commit')
        return r

    def produces(self):
        return ['sheet_seq']

    def transform(self, context):
        ranges = self.sheet_ranges
        update_methods = self.update_methods
        result = context['parse_result']
        if self.commit_range is not None:
            ranges = [*ranges, self.commit_range]
            result.append(context['repo_commit'])
            update_methods = [*update_methods, 'A']
        seq = self.sheet.append_result(
            context['task_id'], ranges, result, update_methods, sheet=self.sub_sheet)
        context['sheet_seq'] = seq


class RenameLogWithSeq(Callback):

    def __init__(self, suffix1=True):
        r"""
        Examples::
            >>> cb = RenameLogWithSeq(suffix1=False)
            >>> cb.transform({'log_file': log_file, 'task_id': 460, 'seq': 1})
            >>> assert log_file.name == "460.log"

            >>> cb = RenameLogWithSeq(suffix1=True)
            >>> cb.transform({'log_file': log_file, 'task_id': 460, 'seq': 1})
            >>> assert log_file.name == "460-1.log"

            >>> cb.transform({'log_file': log_file, 'task_id': 460, 'seq': 2})
            >>> assert log_file.name == "460-2.log"
        """

        self.suffix1 = suffix1

    def requires(self):
        return ['log_file', 'task_id', 'sheet_seq']

    def transform(self, context):
        name = context['task_id']
        seq = context['sheet_seq']
        log_file = context['log_file']
        name = f"{name}" if seq == 1 and not self.suffix1 else f"{name}-{seq}"
        new_log_file = log_file.with_name(name + log_file.suffix)
        copy(log_file, new_log_file)
        context['log_file'] = new_log_file


class PushLogToGitHub(Callback):

    def __init__(self, github, max_retry=3, retry_interval=10):
        r"""
        Examples::
            >>> git_repo = "gourmets/experiments"
            >>> folder = "ImageNet"
            >>> access_token = "aa8f2297d25b4dc6fd3d98411eb3ba53823c4f42"
            >>> github = Github(git_repo, folder, access_token)
            >>> cb = PushLogToGitHub(github)
        """

        self.github = github
        self.max_retry = max_retry
        self.retry_interval = retry_interval

    def requires(self):
        return ['log_file']

    def transform(self, context):
        log_file = context['log_file']
        log_name = log_file.stem
        content = read_text(log_file)
        path = "log/" + log_name + ".log"

        retry_fn(
            lambda: self.github.push(path, content),
            self.max_retry, (GithubException,), self.retry_interval)
