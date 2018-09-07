#!/usr/bin/env python3
"""
git-branch-metrics-collector.py
"""


import argparse
from io import StringIO
import logging
import os
from pprint import pprint
import sh
import shutil
import sys


# Prepare a logger that prints the log level and the log message to stdout
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
        # repo, then something is seriously wrong. Burn it down and start
        # with a clean repo.
        log.warning(f"Deleting invalid git repo found at {repo_path}")
        shutil.rmtree(repo_path)
        clone_the_repo = True
    else:
        log.debug(f"Directory {repo_path} is apparently a git repo")


    if clone_the_repo:
        log.info(f"Cloning {repo_name} ...")
        os.chdir(repos_dir)
        sh.git.clone(repo_url)
    else:
        # The git repo exists, so bring it up to date
        log.info(f"Fetching changes to {repo_name}")
        os.chdir(repo_path)
        sh.git.fetch('--all')

    return repo_path


def fetch_branches(name, repo_path):
    log.info(f"Fetching branches for {name}")

    buf = StringIO()
    sh.git("ls-remote", _out=buf, _cwd=repo_path)

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

    # prepare a dictionary that maps the branch name to the branch's commit ID
    heads_commits = {}
    for line in buf.getvalue().splitlines():
        fields = line.split()

        # skip the HEAD entry
        if fields[-1] == 'HEAD':
            continue

        # only store lines for branches (i.e. heads)
        if 'refs/heads' in fields[-1]:
            heads_commits[fields[-1]] = fields[0]

    buf.close()

    for k in heads_commits.keys():
        log.debug(f"ref {k:40} is commit {heads_commits[k]}")

    return heads_commits


def fetch_branch_authors(branches, repo_path):

    print("    Branch authors:")

    git = sh.git.bake(_cwd=repo_path)

    for ref, commitId in branches.items():
        buf = StringIO()
        git.log("-1", "--pretty=format:'%an'", commitId, _out=buf)
        author = buf.getvalue()
        buf.close()

        pprint(author)
        # print(f"   {author}")
        # print(f"       {ref} most recent author is" + author)



if __name__ == '__main__':

    print("\nExecuting git-branch-metrics-collector.py ...")

    args = parse_cmd_line()
    log.debug(args)

    # This Docker volume holds the repositories cloned by this script.
    repos_dir = '/root/repos'
    if not os.path.isdir(repos_dir):
        log.error(f"A required volume ({repos_dir}) is missing. Exiting.")
        exit()

    repos_list = {
        'gitBranchTestRepo': 'https://gitlab.com/patrickbrooks/gitBranchTestRepo.git',
        'keyrunner':         'https://gitlab.com/rustushki/keyrunner'
    }

    for name in repos_list.keys():
        print(f"\nFor repo {name} :")

        repo_path = prepare_repo(repos_dir, name, repos_list[name])

        branches = fetch_branches(name, repo_path)

        print(f"    Branch count = {len(branches)}")

        fetch_branch_authors(branches, repo_path)



    print("\nDone\n")
