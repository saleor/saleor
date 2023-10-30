#!/usr/bin/env python
"""Notifies about deployment status to a given slack channel.

Dependencies (already shipped by ubuntu-20.04):
- Python 3.6+
- requests package (any version)

Manual Environment Variables (explicit):
- SLACK_WEBHOOK_URL: incoming webhook URL to send payload/message to
- SLACK_MENTION_GROUP_ID: ID of Slack group to be mentioned in case of failure
- JOB_STATUS: status from GitHub's ``job.status``
- JOB_TITLE: the title of the job
- JOB_KIND: kind of job to notify about, by default "build"

Global GitHub Environment Variables (implicit):
- GITHUB_RUN_ID
- GITHUB_REPOSITORY
- GITHUB_ACTOR
"""

import os
import sys

import requests


class JobNotifier:
    JOB_STATUS_COLOR_MAP = {
        "success": "#5DC292",
        "failure": "#FE6E76",
        "cancelled": "#868B8E",
    }

    def __init__(self):
        # The title of the pull request
        self.title: str = os.environ["JOB_TITLE"]

        # Incoming Webhook Endpoint, it is set a the organization level
        # Development notifier configuration is available at: https://api.slack.com/apps/A0210C30YLD/
        self.slack_endpoint = os.environ["SLACK_WEBHOOK_URL"]

        # ID of Slack Group to mention in case of failure
        self.slack_mention_group_id = os.environ["SLACK_MENTION_GROUP_ID"]

        # Workflow Run ID to retrieve the logs permalink of the actual run
        self.run_id: str = os.environ["GITHUB_RUN_ID"]

        # <owner>/<repo>
        self.repository: str = os.environ["GITHUB_REPOSITORY"]

        # The user that triggered the action
        self.author: str = os.environ["GITHUB_ACTOR"]

        # Job Status (success|failure|cancelled)
        self.job_status: str = os.environ["JOB_STATUS"]

        # The kind of job (deployment, release tests, ...)
        self.job_kind: str = os.getenv("JOB_KIND", "build")

    @property
    def run_permalink(self) -> str:
        """Permalink to the current run logs."""
        return f"https://github.com/{self.repository}/actions/runs/{self.run_id}"

    @property
    def job_status_color(self) -> str:
        """Color from Saleor Cloud palette for job status."""
        return self.JOB_STATUS_COLOR_MAP[self.job_status]

    def make_slack_message(self) -> dict:
        status = self.job_status.capitalize()
        mention = self.slack_mention_group_id if status == "Failure" else ""
        # Dev deployment triggered by JohnDoe: Success
        text = f"{self.author} {self.job_kind} result: {status} {mention}"
        message_data = {
            "attachments": [
                {
                    "fallback": text,
                    "pretext": "",
                    "title": f"{self.repository}: {self.title}",
                    "title_link": self.run_permalink,
                    "text": text,
                    "color": self.job_status_color,
                }
            ]
        }
        return message_data

    def send_notification(self) -> None:
        post_data = self.make_slack_message()
        print(f"Notifying slack with payload: {post_data!r}", file=sys.stderr)  # noqa: T201
        response = requests.post(  # nosemgrep: no-requests-lib
            self.slack_endpoint, json=post_data
        )
        response.raise_for_status()


def main():
    JobNotifier().send_notification()


if __name__ == "__main__":
    main()
