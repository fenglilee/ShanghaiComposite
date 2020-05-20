#!/usr/bin/env python
# -*- coding:utf-8 -*-
import tempfile
import git
import git.exc as git_exception
import os
from aops.applications.database.models.repository.repository import FileReview
import shutil
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.exceptions.exception import Error
from aops.applications.database.apis.system.message.message import create_message


def hide_auth_info(username, password, error_info):
    error_info = str(error_info)
    new_info = error_info.replace(username + ":" + password + '@', '****:****@')
    return new_info


def git_clone_to_dir(app, git_tmp_dir, parts, branch):
    gitlab_ip = app.config.get('GITLAB_URL').split('//')[-1]
    url_list = parts[1].split('/')[1:]
    url_list.insert(0, gitlab_ip)
    parts[1] = '/'.join(url_list)
    username = app.config.get("GITLAB_USER", "root")
    email = app.config.get("GITLAB_EMAIL", "root@aops.com")
    password = app.config.get("GITLAB_PASSWORD", "Pwd123$%^")
    repo_url = '{}://{}:{}@{}'.format(parts[0], username, password, parts[1])
    app.logger.debug(repo_url)
    app.logger.debug(git_tmp_dir)
    try:
        git.Repo.clone_from(repo_url, git_tmp_dir, branch=branch)
    except git_exception.GitError as e:
        info = hide_auth_info(username, password, e)
        app.logger.debug(u"{}".format(info))
        app.logger.error(u"{}".format(e.message))
        shutil.rmtree(git_tmp_dir)

    # # git repo init
    repo = git.Repo(git_tmp_dir)
    with repo.config_writer() as cw:
        cw.set_value('user', 'name', username)
        cw.set_value('user', 'email', email)
        cw.release()
    return repo


def copy_files(app, path, files, git_tmp_dir):
    # copy path init
    if path == '/':
        copy_path = git_tmp_dir
    elif path.startswith('/'):
        copy_path = git_tmp_dir + path
    else:
        copy_path = git_tmp_dir + '/' + path
    try:
        # copy files
        for file_item in files:
            server_local_path = file_item.get('server_path')
            app.logger.debug("file's server_path: {}".format(server_local_path))
            for root, dirs, files in os.walk(server_local_path):
                file_relative_path_list = [root + "/" + f for f in files]
                for f in file_relative_path_list:
                    if f:
                        shutil.copy(f, copy_path)
                        app.logger.info("copy file src: {} , dest: {}".format(f, copy_path))
    except Exception as e:
        app.logger.error(u"file_controller copy files occur error: {}".format(e.message))


def file_controller(app, project_id, path, files, comment, review_id, target_branch, creator):
    """

    Args:
        project_id:
        comment: commit comment
        files: uploaded files list
        comment: submit comments
        review_id: file's review id，
        target_branch:
    Returns:

    """
    # __init__
    with app.app_context():
        repository = Repostiory(gitlab_url=app.config.get('GITLAB_URL'),
                                private_token=app.config.get('GITLAB_TOKEN'),
                                email=app.config.get('GITLAB_EMAIL', 'aops@example.com'),
                                user=creator
                                )
        try:
            project = repository.get_project_by_id(project_id)
        except Error as e:
            app.logger.error(e.message)
        http_url_to_repo = project.attributes.get('http_url_to_repo')
        parts = http_url_to_repo.split('://')
        app.logger.debug(parts)

        git_tmp_dir = tempfile.mkdtemp()

        try:
            if review_id is None:
                # git checkout project to git_tmp_dir
                tmp_branch_name = 'master'
            else:
                # create tmp branch
                tmp_branch_name = repository.generate_tmp_branch()
                app.logger.debug("tmp_branch_name: {}".format(tmp_branch_name))
                branch = project.branches.create({'branch': tmp_branch_name, 'ref': target_branch})
                app.logger.debug("branch: {}".format(branch.attributes))

            # git checkout project (branch: tmp_branch_name) to git_tmp_dir
            repo = git_clone_to_dir(app, git_tmp_dir, parts, tmp_branch_name)
            copy_files(app, path, files, git_tmp_dir)

            # git add & commit files
            repo.git.execute(['git', 'add', '*'])
            repo.git.execute(
                    ['git', 'commit', '-a', '-m', 'system commit {}'.format(comment)])
            commit_sha = repo.head.commit.hexsha
            repo.git.push()

            if review_id:
                # create merge_id
                mr = repository.create_merge_request_by_project_id(project_id,
                                                                   source_branch=tmp_branch_name,
                                                                   target_branch=target_branch,
                                                                   title="aops system merge request, branch: "
                                                                         + tmp_branch_name)
                merge_id = mr.get_id()
                app.logger.debug("merge_id: {}".format(merge_id))
                review_item = FileReview.query.filter_by(id=review_id).one()
                data = {
                    'merge_id': merge_id,
                    'commit_sha': commit_sha,
                    'status': 'pending'
                }
                updated = review_item.update(**data)
                message_data = {
                    'classify': 1,  # 0: notification, 1:confirmation
                    'risk_level': 0,  # 0:low, 1:middle, 2:high
                    'content': "Git file async operation success, project: {}， target_branch: {}, status: "
                               "waiting for review".format(project.name, target_branch),
                    'status': 0,  # 0: confirmed, 1:non-confirmed, 2:unconfirmed,
                    'usernames': [creator]
                }
                create_message(**message_data)
                app.logger.debug(updated.to_dict())
        except Exception as e:
            message_data = {
                'classify': 1,  # 0: notification, 1:confirmation
                'risk_level': 2,  # 0:low, 1:middle, 2:high
                'content': "Git file async operation occur error: {}".format(e),
                'status': 0,  # 0: confirmed, 1:non-confirmed, 2:unconfirmed,
                'usernames': [creator]
            }
            create_message(**message_data)
            app.logger.error("Git file occur error:{}".format(e))
        finally:
            try:
                shutil.rmtree(git_tmp_dir)
            except Exception as e:
                app.logger.errror("Delete git tmp file occur error: {}".format(e.message))
