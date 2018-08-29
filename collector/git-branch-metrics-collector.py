#!/usr/bin/env python3
"""
git-branch-metrics-collector.py
"""

import argparse
import logging
import os
import sh
import sys

# Prepare the logger
log = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
log.addHandler(stdout_handler)


def parse_cmd_line():
    parser = argparse.ArgumentParser(description="Count metrics in git repos")
    parser.add_argument('--path',
                        help="absolute path inside container of repos' parent directory",
                        default="/root/Git")
    parser.add_argument('--log',
                        help='set logging level (default is warn)',
                        choices=['info', 'debug'],
                        default='warn')
    args = parser.parse_args()

    if args.log == 'debug':
        log.setLevel(logging.DEBUG)
    elif args.log == 'info':
        log.setLevel(logging.INFO)
    else:
        # default log level is WARN
        log.setLevel(logging.WARN)

    return {'repo_path': args.path}


def count_branches(git):

    # branch_list includes an extra line of output from the 'git branch'
    # command. strip() does not get rid of it.
    branch_list = git.branch('-a').split('\n')
    log.debug(branch_list)

    print('Count of branches in repo', repo, '=', len(branch_list)-1)
    for branch in branch_list:
        log.info(branch.strip())


def collect_repo_stats(repo_path, repo):

    repo_path = os.path.join(repo_path, repo)

    if not os.path.isdir(repo_path):
        log.error("Repo path is not a directory = %s" % repo_path)

    else:
        git = sh.git.bake(_cwd=repo_path)

        # receive new branches and delete old branches
        git.fetch('--all', '--prune')

        count_branches(git)


if __name__ == '__main__':

    print("\nExecuting git-branch-metrics-collector.py ...\n")

    args = parse_cmd_line()
    log.debug(args)

    repos = [
        'git-branch-metrics',
        'temp'
    ]

    for repo in repos:
        collect_repo_stats(args['repo_path'], repo)

    print("\nDone\n")
