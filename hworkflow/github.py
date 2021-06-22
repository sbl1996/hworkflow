from pathlib import Path

from github import Github as PyGithub, InputGitTreeElement


class Github:

    def __init__(self, repo_name, folder, access_token) -> None:
        self.repo_name = repo_name
        self.folder = folder
        self.access_token = access_token

        self.github = PyGithub(access_token)
        self.repo = self.github.get_repo(self.repo_name)

    def fetch(self, path):
        path = self.folder + "/" + path
        return self.repo.get_contents(path).decoded_content.decode()

    def push(self, path, content):
        repo = self.repo
        master_ref = repo.get_git_ref('heads/main')
        master_sha = master_ref.object.sha
        base_tree = repo.get_git_tree(master_sha)
        elements = [
            InputGitTreeElement(f"{self.folder}/{path}", '100644', 'blob', content)
        ]
        tree = repo.create_git_tree(elements, base_tree)
        parent = repo.get_git_commit(master_sha)
        commit_message = f'Add {Path(path).name} for {self.folder}'
        commit = repo.create_git_commit(commit_message, tree, [parent])
        master_ref.edit(commit.sha)