import subprocess
from typing import Any

import click
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "test"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--commit",
            dest="commit",
        )
        parser.add_argument(
            "--branch",
            dest="branch",
        )
        parser.add_argument(
            "--from",
            dest="from",
            default="3.14",
            help="The lowest version of Saleor to where you want to port patch. Defaults to 3.14.",
        )
        parser.add_argument(
            "--to",
            dest="to",
            default="main",
            help="The latest version of Saleor to where you want to port patch. Defaults to main.",
        )

    def handle(self, *args: Any, **options: Any):
        commit_name = options["commit"]
        branch_name = options["branch"]
        first_version = options["from"]
        last_version = options["to"]

        self.validate_version(first_version)
        self.validate_version(last_version)

        subprocess.run(["git", "fetch"])

        current_version = self.get_branch_version(first_version, last_version)
        while current_version is not None:
            self.create_branch(branch_name, current_version)
            self.process_cherry_picking(commit_name)
            if current_version != "main":
                major, minor = current_version.split(".")
                next_version = major + str(int(minor) + 1)
                current_version = self.get_branch_version(next_version, last_version)
            else:
                current_version = None

    def create_branch(self, branch_name, version):
        if version == "main":
            target_branch = branch_name + "-main"
        else:
            major, minor = version.split(".")
            target_branch = branch_name + "-" + major + minor
        try:
            subprocess.run(
                ["git", "branch", target_branch, version],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            if b"already exists" in e.stderr:
                if not click.confirm(
                    f"Branch name {target_branch} already exists. Do you want to continue?",
                    default=True,
                ):
                    exit()
            else:
                self.exit_script(e.stderr)
        subprocess.run(["git", "switch", target_branch])

    def process_cherry_picking(self, commit_name):
        try:
            subprocess.run(
                ["git", "cherry-pick", commit_name], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            if b"could not apply" in e.stderr:
                click.pause(
                    "Could not apply the commit. Resolve the conflicts and then press any key to continue."
                )
            else:
                self.exit_script(e.stderr)
        subprocess.run(["python", "manage.py", "makemigrations", "--merge"])

    def get_branch_version(self, version, last_version):
        if last_version == "main" or version <= last_version:
            version_exists = self.branch_exits(version)
            if last_version == "main" and not version_exists:
                return "main"
            return version
        return None

    def branch_exits(self, version):
        result = subprocess.check_output(["git", "branch", "-l", version], text=True)
        return version in result

    def exit_script(self, error):
        exit(f"Unexpected error during branch creation {error}")

    def validate_version(self, version):
        try:
            _, _ = version.split(".") if version != "main" else (0, 0)
        except ValueError:
            self.exit_script(
                f"Provided {version} is in wrong format. Please use `major.minor`."
            )
