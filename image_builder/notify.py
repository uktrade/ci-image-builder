import os
from enum import Enum

from slack_sdk import WebClient
from slack_sdk.models import blocks

from image_builder.codebase.codebase import Codebase
from image_builder.progress import Progress


class JobState(dict):
    def __init__(self):
        super().__init__()
        self[Phase.SETUP] = PhaseState.PENDING
        self[Phase.BUILD] = PhaseState.PENDING
        self[Phase.PUBLISH] = PhaseState.PENDING
        self[Phase.DONE] = PhaseState.PENDING

    def get_current_phase(self):
        if self[Phase.SETUP] == PhaseState.RUNNING:
            return Phase.SETUP
        if self[Phase.BUILD] == PhaseState.RUNNING:
            return Phase.BUILD
        if self[Phase.PUBLISH] == PhaseState.RUNNING:
            return Phase.PUBLISH
        return Phase.DONE


class PhaseState(Enum):
    PENDING = "pending :large_blue_circle:"
    RUNNING = "running :hourglass_flowing_sand:"
    SUCCESS = "success :large_green_circle:"
    FAILURE = "failure :red_circle:"


class Phase(Enum):
    SETUP = "setup"
    BUILD = "build"
    PUBLISH = "publish"
    DONE = "done"


class Settings:
    channel: str
    workspace: str
    build_arn: str


class Notify:
    codebase: Codebase
    reference: str
    state: JobState
    settings: Settings

    def __init__(self, codebase: Codebase):
        self.state = JobState()
        self.settings = Settings()
        self.codebase = codebase
        try:
            self.slack = WebClient(token=os.environ["SLACK_TOKEN"])
            self.settings.channel = os.environ["SLACK_CHANNEL_ID"]
            self.settings.build_arn = os.environ["CODEBUILD_BUILD_ARN"]
        except KeyError as e:
            raise ValueError(f"{e} environment variable must be set")

    def post_progress(self, progress: Progress):
        message_blocks = [
            blocks.SectionBlock(
                text=blocks.TextObject(
                    type="mrkdwn",
                    text=f"*Building {self.codebase.revision.get_repository_name()}@{self.codebase.revision.commit}*",
                ),
            ),
            blocks.ContextBlock(
                elements=[
                    blocks.TextObject(
                        type="mrkdwn",
                        text=f"*Repository*: <{self.codebase.revision.get_repository_url()}|{self.codebase.revision.get_repository_name()}>",
                    ),
                    blocks.TextObject(
                        type="mrkdwn",
                        text=f"*Revision*: <{self.codebase.revision.get_repository_url()}/commit/{self.codebase.revision.commit}|{self.codebase.revision.commit}>",
                    ),
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
                    blocks.TextObject(
                        type="mrkdwn", text=f"<{self.get_build_url()}|Build Logs>"
                    ),
                ]
            ),
        ]
        if hasattr(self, "reference"):
            response = self.slack.chat_update(
                channel=os.environ["SLACK_CHANNEL_ID"],
                blocks=message_blocks,
                ts=self.reference,
                text=f"Building: {self.codebase.revision.get_repository_name()}@{self.codebase.revision.commit}",
                unfurl_links=False,
                unfurl_media=False,
            )
            self.reference = response["ts"]
        else:
            response = self.slack.chat_postMessage(
                channel=os.environ["SLACK_CHANNEL_ID"],
                blocks=message_blocks,
                text=f"Building: {self.codebase.revision.get_repository_name()}@{self.codebase.revision.commit}",
                unfurl_links=False,
                unfurl_media=False,
            )
            self.reference = response["ts"]

    def post_job_comment(self, message):
        self.slack.chat_postMessage(
            channel=os.environ["SLACK_CHANNEL_ID"],
            blocks=[
                blocks.SectionBlock(text=blocks.TextObject(type="mrkdwn", text=line))
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
