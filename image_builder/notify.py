import os
from typing import List

from slack_sdk import WebClient
from slack_sdk.models import blocks

from image_builder.codebase.codebase import Codebase
from image_builder.progress import Progress
from image_builder.utils.arn_parser import ARN


class Settings:
    channel: str
    workspace: str
    build_arn: str


class Notify:
    codebase: Codebase
    reference: str | None
    settings: Settings

    def __init__(self, send_notifications: bool = True):
        self.settings = Settings()
        self.send_notifications = send_notifications
        self.reference = None

        if self.send_notifications:
            try:
                self.settings.build_arn = os.environ["CODEBUILD_BUILD_ARN"]
                self.slack = WebClient(token=os.environ["SLACK_TOKEN"])
                self.settings.channel = os.environ["SLACK_CHANNEL_ID"]
            except KeyError as e:
                raise ValueError(f"{e} environment variable must be set")

    def post_build_progress(self, progress: Progress, codebase: Codebase):
        if self.send_notifications:
            message_headline = (
                f"*Building {codebase.revision.get_repository_name()}@"
                f"{codebase.revision.commit}*"
            )
            message_repository = (
                f"*Repository*: <{codebase.revision.get_repository_url()}|"
                f"{codebase.revision.get_repository_name()}>"
            )
            message_revision = (
                f"*Revision*: <{codebase.revision.get_repository_url()}/commit/"
                f"{codebase.revision.commit}|{codebase.revision.commit}>"
            )
            message_build_logs = f"<{self.get_build_url()}|Build Logs>"

            message_blocks = [
                blocks.SectionBlock(
                    text=blocks.TextObject(type="mrkdwn", text=message_headline),
                ),
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(type="mrkdwn", text=message_repository),
                        blocks.TextObject(type="mrkdwn", text=message_revision),
                        blocks.TextObject(type="mrkdwn", text=message_build_logs),
                    ]
                ),
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(
                            type="mrkdwn", text=f'{progress.get_phase("setup")}'
                        ),
                        blocks.TextObject(
                            type="mrkdwn", text=f'{progress.get_phase("build")}'
                        ),
                        blocks.TextObject(
                            type="mrkdwn", text=f'{progress.get_phase("publish")}'
                        ),
                        blocks.TextObject(
                            type="mrkdwn", text=f'{progress.get_phase("deploy")}'
                        ),
                    ]
                ),
            ]

            if self.reference is None:
                response = self.slack.chat_postMessage(
                    channel=os.environ["SLACK_CHANNEL_ID"],
                    blocks=message_blocks,
                    text=f"Building: {codebase.revision.get_repository_name()}@{codebase.revision.commit}",
                    unfurl_links=False,
                    unfurl_media=False,
                )
                self.reference = response["ts"]
            else:
                response = self.slack.chat_update(
                    channel=os.environ["SLACK_CHANNEL_ID"],
                    blocks=message_blocks,
                    ts=self.reference,
                    text=f"Building: {codebase.revision.get_repository_name()}@{codebase.revision.commit}",
                    unfurl_links=False,
                    unfurl_media=False,
                )
                self.reference = response["ts"]

    def post_job_comment(
        self, title: str, message: List[str], send_to_main_channel=False
    ):
        if self.send_notifications:
            response = self.slack.chat_postMessage(
                channel=os.environ["SLACK_CHANNEL_ID"],
                blocks=[
                    blocks.SectionBlock(
                        text=blocks.TextObject(type="mrkdwn", text=line)
                    )
                    for line in message
                    if line
                ],
                text=title,
                reply_broadcast=send_to_main_channel,
                unfurl_links=False,
                unfurl_media=False,
                thread_ts=self.reference,
            )
            return response["ts"]

    def get_build_url(self):
        try:
            arn = ARN(self.settings.build_arn)
            url = (
                "https://{region}.console.aws.amazon.com/codesuite/codebuild/{account}/projects/{"
                "project}/build/{project}%3A{build_id}"
            )
            return url.format(
                region=arn.region,
                account=arn.account_id,
                project=arn.project.replace("build/", ""),
                build_id=arn.build_id,
            )
        except ValueError:
            return ""
