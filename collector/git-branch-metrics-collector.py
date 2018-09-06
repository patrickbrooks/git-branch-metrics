#!/usr/bin/env python3
"""
git-branch-metrics-collector.py
"""

import argparse
from git import Repo, NoSuchPathError, InvalidGitRepositoryError
import logging
import os
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

    parser.add_argument('--log',
                        help='set logging level (default is warn)',
                        choices=['info', 'debug', 'warn'],
                        default='warn')
    args = parser.parse_args()

    # default log level of warn is set in --log add_argument, above
    if args.log == 'debug':
        log.setLevel(logging.DEBUG)
    elif args.log == 'info':
        log.setLevel(logging.INFO)
    elif args.log == 'warn':
        log.setLevel(logging.WARN)
    else:
        log.error("Unexpected log level = {}\nExiting.\n".format(args.log))
        exit()

    return {'foo': 'args.bar'}


def prepare_repo(repos_dir, repo_name, repo_url):
    # Confirm that a git repo exists at the given local directory. If it does
    # not exist, then attempt to clone it. If it already exists, then
    # fetch new branches and prune old branches.

    repo_path = os.path.join(repos_dir, repo_name)
    log.debug("Preparing repo {}".format(repo_name))

    repo = None
    try:
        repo = Repo(repo_path)
    except NoSuchPathError:
        # We will clone the repo below so no big deal
        log.debug("Git repo not found at {}".format(repo_path))
    except InvalidGitRepositoryError:
        # Delete the invalid repo and then re-clone it below
        log.warning("Deleting invalid git repo found at {}".format(repo_path))
        shutil.rmtree(repo_path)

    if (repo is None) or repo.bare:
        log.info("Cloning {}".format(repo_path))
        repo = Repo.clone_from(repo_url, repo_path)
    else:
        log.info("Fetching updates to {}".format(repo_name))
        origin = repo.remote('origin')
        origin.fetch(prune=True)

    return repo


def fetch_branches(name, repo):
    log.info("Fetching branches in {}".format(name))

    branches = repo.git.branch('-r').split('\n')

    # To make a more accurate list, remove the HEAD reference
    # (ex. "origin/HEAD -> origin/master")
    branches[:] = [x for x in branches if 'origin/HEAD ->' not in x]

    for branch in branches:
        log.debug("Found {}".format(branch))

    return branches


def fetch_branch_details(branch, name, repo):

    log.debug("Finding author of HEAD commit on {}'s {} branch".format(name, branch))

    foo = repo.git.lsremote()
    print(foo)





if __name__ == '__main__':

    print("\nExecuting git-branch-metrics-collector.py ...\n")

    args = parse_cmd_line()
    log.debug(args)

    # This Docker volume holds the repositories cloned by this script.
    repos_dir = '/root/repos'
    if not os.path.isdir(repos_dir):
        log.error("A required mount is missing: {}\nExiting.\n".format(repos_dir))
        exit()

    repos_list = {
        'gitBranchTestRepo': 'https://gitlab.com/patrickbrooks/gitBranchTestRepo.git',
        'keyrunner':         'https://gitlab.com/rustushki/keyrunner'
    }

    for name in repos_list.keys():
        print("\nFor repo {} :".format(name))

        repo = prepare_repo(repos_dir, name, repos_list[name])

        branches = fetch_branches(name, repo)
        print("    Number of branches = {}".format(len(branches)))

        for branch in branches:
            fetch_branch_details(branch, name, repo)



    print("\nDone\n")
