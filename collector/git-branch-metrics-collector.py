#!/usr/bin/env python3
"""
git-branch-metrics-collector.py
"""


import argparse
import collections
from io import StringIO
import logging
import os
from pprint import pprint
from sh import git
import shutil
import sys


# Prepare a logger that prints to stdout
log = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
log.addHandler(stdout_handler)


def parse_cmd_line():
    parser = argparse.ArgumentParser(
        description="Collect metrics about branches in git repos")

    parser.add_argument('--loglevel',
                        help='set logging level (default is warn)',
                        choices=['info', 'debug', 'warn'],
                        default='warn')
    args = parser.parse_args()

    # default log level of warn is set in --log add_argument, above
    if args.loglevel == 'debug':
        log.setLevel(logging.DEBUG)
    elif args.loglevel == 'info':
        log.setLevel(logging.INFO)
    elif args.loglevel == 'warn':
        log.setLevel(logging.WARN)
    else:
        log.error("Unexpected log level = {args.loglevel}\nExiting.\n")
        exit()

    # save this for later
    return {'foo': 'args.bar'}


def prepare_repo(repos_dir, repo_name, repo_url):
    # Confirm that a git repo exists at the given local directory. If it does
    # not exist, then attempt to clone it. If it already exists, then
    # fetch new branches and prune old branches.

    log.debug("Preparing repo " + repo_name)

    repo_path = os.path.join(repos_dir, repo_name)
    dot_git_path = os.path.join(repo_path, '.git')

    clone_the_repo = False
    if not os.path.isdir(repo_path):
        log.warning(f"Directory {repo_path} not found")
        clone_the_repo = True
    elif not os.path.isdir(dot_git_path):
        # If we find a directory in our mounted volume that is not a git
        # repo, then something is seriously wrong. Delete the directory and
        # start again with a clean repo.
        log.warning(f"Deleting invalid git repo found at {repo_path}")
        shutil.rmtree(repo_path)
        clone_the_repo = True
    else:
        log.debug(f"Directory {repo_path} is apparently a git repo")


    if clone_the_repo:
        log.info(f"Cloning {repo_name} ...")
        os.chdir(repos_dir)
        git.clone(repo_url)
    else:
        # The git repo exists, so bring it up to date
        log.info(f"Fetching changes to {repo_name}")
        os.chdir(repo_path)
        git.fetch('--all')

    return repo_path


def fetch_branches(name, repo_path):
    log.info(f"Fetching branches for {name}")

    buf = StringIO()
    git("ls-remote", _out=buf, _cwd=repo_path)

    """
    Output of ls-remote looks like:
    $ git ls-remote
    8772d940766815ff9cb8f7ca1b46d4a726dee75d	HEAD
    b16e6b4dee93915fe92b4f7c41b214b4635ef98a	refs/heads/develop
    17c2cd0bb85f2095cee5798fc654ec6a59bbe6c3	refs/heads/feature/player-not-bound-to-grid
    8772d940766815ff9cb8f7ca1b46d4a726dee75d	refs/heads/master
    39e176cb7f83a712196aae8e1f4c51dd8f2481f9	refs/tags/v1.4.1
    8772d940766815ff9cb8f7ca1b46d4a726dee75d	refs/tags/v1.5.0
    """

    # prepare a dictionary that maps each branch name to the branch's commit ID
    heads_commits = {}
    for line in buf.getvalue().splitlines():
        fields = line.split()

        if len(fields) != 2:
            log.warning(f"Unexpected number of fields in {line}. Skipping ...")
            continue

        # skip the HEAD entry because it is a duplicate of another entry
        if fields[-1] == 'HEAD':
            continue

        # only store lines for branches (i.e. heads) ... not tags
        if 'refs/heads' in fields[-1]:
            head_name = fields[-1].replace('refs/heads/', '')
            heads_commits[head_name] = fields[0]

    buf.close()

    for k in heads_commits.keys():
        log.debug(f"ref {k:20} is commit {heads_commits[k]}")

    return heads_commits


def fetch_branch_authors(branches, repo_path):

    print("    Branch authors:")

    gitsh = git.bake(_cwd=repo_path, _tty_out=False)

    for ref, commitId in branches.items():
        buf = StringIO()
        gitsh.log("-1", "--pretty=format:%an", commitId, _out=buf)
        author = buf.getvalue()
        buf.close()

        print(f"        {ref:20} most recent author is {author}")


def base_branch_exists(base_branch, branches, name):

    rc = False

    if base_branch in branches:
        log.info(f"        {base_branch} exists in {name} repo")
        rc = True
    else:
        log.warning(f"        {base_branch} does not exist in {name} repo.")

    return rc


def fetch_first_commit_id(branch, base_branch, commitId):
    """
    From https://stackoverflow.com/questions/18407526/git-how-to-find-first-commit-of-specific-branch/32870852#32870852

    A-B-C-D-E (base_branch)
         \
          F-G-H (branch)

    We are looking for commit F.

    git log base_branch..branch --oneline | tail -1

    "dot-dot gives you all of the commits that the branch has that base_branch
    doesn't have." These commits are listed in reverse topological order, so
    the last one in the list is the first commit on the branch.

    The downside of this approach is that we must specify the base_branch
    from which 'branch' was branched. Ideally, base_branch wouldn't be
    required.

    This technique is good enough to start. Other options exist if this doesn't
    hold up.
    """

    first_commit_id = None

    buf = StringIO()
    gitsh = git.bake(_cwd=repo_path, _tty_out=False)
    gitsh.log(f"{base_branch}..{commitId}", "--format=%h %s", _out=buf)
    """ Output looks like:
    $ git log master..20180905-foo --oneline
    124e842 2nd commit on 20180905-foo
    cdb7133 1st commit on 20180905-foo
    """

    lines = buf.getvalue().splitlines()
    if len(lines) <= 0:
        log.debug(f"Found no commits on {branch} that are not on {base_branch}")
    else:
        # The first commit on the branch is listed last in the output, so index
        # the output by [-1] to find it.
        # Split the line into only 2 parts: the commitId and the commit subject.
        fields = lines[-1].split(' ', 1)
        if len(fields) < 2:
            log.warning(f"Unexpected number of fields = {len(fields)}. Skipping...")
        else:
            log.debug(f"First commit on {branch} is {fields[0]} w/ subject '{fields[1]}'")
            first_commit_id = fields[0]

    buf.close()

    return first_commit_id


def fetch_commit_date(commit_id, repo_path):

    commit_date = None

    buf = StringIO()
    gitsh = git.bake(_cwd=repo_path, _tty_out=False)
    gitsh.log("-n 1", "--format=%ci", commit_id, _out=buf)
    lines = buf.getvalue().splitlines()
    if len(lines) != 1:
        log.warning(f"Unexpected git log output: {lines}. Skipping ...")
    else:
        log.debug(f"First commit was created at {lines[0]}")
        commit_date = lines[0]

    return commit_date


def fetch_branch_ages(branches, base_branch, repo_path):

    print("    Branch ages:")

    for branch, commitId in branches.items():

        if branch == base_branch:
            # skip when master == master, for example
            log.debug(f"Skipping {branch} == {base_branch}")
            continue

        # Find the first commit on branch that does not exist on base_branch. We
        # will use the date of this commit (if it exists) as the branch
        # creation date
        first_branch_commit = fetch_first_commit_id(branch, base_branch, commitId)

        # Now use the commitId to find the commit date
        if first_branch_commit:
            branch_date = fetch_commit_date(first_branch_commit, repo_path)
            print(f"        {branch:20} created on {branch_date}")
        else:
            print(f"        No commits on {branch} that are not on {base_branch}")


def fetch_merged_branches(branches, base_branch, repo_path):

    print(f"    Branches merged into {base_branch}:")
    merged_branch_count = 0

    gitsh = git.bake(_cwd=repo_path, _tty_out=False)

    for branch, commitId in branches.items():

        # skip when master == master, for example
        if branch == base_branch:
            log.debug(f"Skipping {branch} == {base_branch}")
            continue

        buf = StringIO()
        gitsh.branch("-a", "--contains", commitId, _out=buf)
        lines = buf.getvalue()
        buf.close()

        if base_branch in lines:
            print(f"        {branch:20} has been merged into {base_branch}")
            merged_branch_count += 1
        else:
            log.debug(f"        {branch:20} has not yet been merged into {base_branch}")

    if merged_branch_count == 0:
        print(f"        No merged branches found")


if __name__ == '__main__':

    print("\nExecuting git-branch-metrics-collector.py ...")

    args = parse_cmd_line()
    log.debug(args)

    # This Docker volume holds the repositories cloned by this script.
    repos_dir = '/home/gbu/repos'
    if not os.path.isdir(repos_dir):
        log.error(f"A required volume ({repos_dir}) is missing. Exiting.")
        exit()

    # for now, hardcode some public repos. Later, pull these from configuration
    # file or database table
    repos_list = collections.defaultdict(dict)
    repos_list['gitBranchTestRepo']['url'] = 'https://gitlab.com/patrickbrooks/gitBranchTestRepo.git'
    repos_list['gitBranchTestRepo']['base_branch'] = 'master'
    repos_list['keyrunner']['url'] = 'https://gitlab.com/rustushki/keyrunner'
    repos_list['keyrunner']['base_branch'] = 'master'
    repos_list['flask']['url'] = 'https://github.com/pallets/flask.git'
    repos_list['flask']['base_branch'] = 'develop'
    repos_list['cpython']['url'] = 'https://github.com/python/cpython.git'
    repos_list['cpython']['base_branch'] = 'develop'

    for name in repos_list.keys():
        print(f"\nFor repo {name} :")

        repo_path = prepare_repo(repos_dir, name, repos_list[name]['url'])

        branches = fetch_branches(name, repo_path)
        print(f"    Branch count = {len(branches)}")

        fetch_branch_authors(branches, repo_path)

        if not base_branch_exists(repos_list[name]['base_branch'], branches, name):
            print(f"\n        Skipping determination of branch ages and merged branches.")
        else:
            fetch_branch_ages(branches, repos_list[name]['base_branch'], repo_path)

            fetch_merged_branches(branches, repos_list[name]['base_branch'], repo_path)

    print("\nDone\n")
