import os

from slack_sdk import WebClient
from slack_sdk.models import blocks

from image_builder.codebase.codebase import Codebase
from image_builder.progress import Progress


class Settings:
    channel: str
    workspace: str
    build_arn: str


class Notify:
    codebase: Codebase
    reference: str | None
    settings: Settings

    def __init__(self, codebase: Codebase, send_notifications: bool = True):
        self.settings = Settings()
        self.codebase = codebase
        self.send_notifications = send_notifications
        self.reference = None

        if self.send_notifications:
            try:
                self.slack = WebClient(token=os.environ["SLACK_TOKEN"])
                self.settings.channel = os.environ["SLACK_CHANNEL_ID"]
                self.settings.build_arn = os.environ["CODEBUILD_BUILD_ARN"]
            except KeyError as e:
                raise ValueError(f"{e} environment variable must be set")

    def post_progress(self, progress: Progress):
        if self.send_notifications:
            message_headline = (
                f"*Building {self.codebase.revision.get_repository_name()}@"
                f"{self.codebase.revision.commit}*"
            )
            message_repository = (
                f"*Repository*: <{self.codebase.revision.get_repository_url()}|"
                f"{self.codebase.revision.get_repository_name()}>"
            )
            message_revision = (
                f"*Revision*: <{self.codebase.revision.get_repository_url()}/commit/"
                f"{self.codebase.revision.commit}|{self.codebase.revision.commit}>"
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
                    ]
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f'{progress.get_phase("setup")}'
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f'{progress.get_phase("build")}'
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f'{progress.get_phase("publish")}'
                    )
                ),
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(type="mrkdwn", text=message_build_logs),
                    ]
                ),
            ]
            if self.reference is None:
                response = self.slack.chat_postMessage(
                    channel=os.environ["SLACK_CHANNEL_ID"],
                    blocks=message_blocks,
                    text=f"Building: {self.codebase.revision.get_repository_name()}@{self.codebase.revision.commit}",
                    unfurl_links=False,
                    unfurl_media=False,
                )
                self.reference = response["ts"]
            else:
                response = self.slack.chat_update(
                    channel=os.environ["SLACK_CHANNEL_ID"],
                    blocks=message_blocks,
                    ts=self.reference,
                    text=f"Building: {self.codebase.revision.get_repository_name()}@{self.codebase.revision.commit}",
                    unfurl_links=False,
                    unfurl_media=False,
                )
                self.reference = response["ts"]

    def post_job_comment(self, message):
        if self.send_notifications:
            self.slack.chat_postMessage(
                channel=os.environ["SLACK_CHANNEL_ID"],
                blocks=[
                    blocks.SectionBlock(
                        text=blocks.TextObject(type="mrkdwn", text=line)
                    )
                    for line in message
                    if line
                ],
                text=f"Build: {self.codebase.revision.get_repository_name()}@{self.codebase.revision.commit} update",
                unfurl_links=False,
                unfurl_media=False,
                thread_ts=self.reference,
            )

    def get_build_url(self):
        build_arn = self.settings.build_arn
        _, _, _, region, account, project, build_id = build_arn.split(":")
        url = (
            "https://{region}.console.aws.amazon.com/codesuite/codebuild/{account}/projects/{"
            "project}/build/{project}%3A{build_id}"
        )
        return url.format(
            region=region,
            account=account,
            project=project.replace("build/", ""),
            build_id=build_id,
        )
