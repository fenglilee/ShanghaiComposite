#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app as app
import git
import git.exc as git_exception


class GitPython(object):
    """
    Use python do some git operations
    Current just base class.
    """

    def __init__(self, workspace, branch_name="master"):
        """
        Args:
            workspace:
            branch_name:
        """
        self.username = app.config.get('GITLAB_USER')
        self.user_email = app.config.get('GITLAB_EMAIL')
        self.workspace = workspace
        self.branch_name = branch_name
        self.repo = git.Repo(self.workspace)
        # init username and email for git
        with self.repo.config_write() as cw:
            cw.set_value('user', 'name', self.username)
            cw.set_value('user', 'email', self.user_email)
            cw.release()

    def git_commit(self, commits="update"):
        """
        Args:
            commits:
        Returns:

        """
        try:
            # repo.git.checkout(branch_name)
            self.repo.git.execute(
                ['git', 'add', '*', self.branch_name])
            self.repo.git.execute(
                ['git', 'commit', '-a', '-m', 'system commit {}'.format(commits),
                 self.branch_name])
            return {"IsSuccess": True}
        except git_exception.GitError as e:
            return {"IsSuccess": False, "Errmsg": str(e)}

    def git_push(self):
        """
        Returns:

        """
        try:
            self.repo.git.push()
            return {"IsSuccess": True}
        except git_exception.GitError as e:
            return {"IsSuccess": False, "Errmsg": str(e)}
