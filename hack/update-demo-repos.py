#!/usr/bin/env python3

import argparse
import shutil
import tempfile
from pathlib import Path

import git
import yaml


def get_args_config() -> dict:
    """Turn parse arguments into a config"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config", type=Path, required=True, help="The location of your config"
    )

    parser.add_argument(
        "--force-push",
        action="store_true",
        help="force push the changes",
    )

    parser.add_argument(
        "--no-cleanup",
        action="store_false",
        help="don't automatically delete the local repo clone",
    )

    return vars(parser.parse_args())


def run():
    args = get_args_config()

    f = open(args["config"])

    yaml_file = yaml.safe_load(f)

    for repo_dict in yaml_file["repos"]:
        temp_dir = tempfile.mkdtemp()
        repo_url = repo_dict["url"]
        print(temp_dir)
        repo = git.Repo.clone_from(repo_url, temp_dir)
        for branch_structure in repo_dict["branch-structure"]:
            for upstream_branch in branch_structure:
                for downstream_branch in branch_structure[upstream_branch]:
                    repo.git.checkout(downstream_branch)
                    repo.git.pull("origin")
                    repo.git.rebase(upstream_branch, X="theirs")
                    repo.git.push("origin", downstream_branch, force=args["force_push"])

        if args["no_cleanup"]:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    run()
