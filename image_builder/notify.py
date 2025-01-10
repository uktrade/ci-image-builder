# import logging
import os
import sys
from typing import List

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.models import blocks

from image_builder.progress import Progress
from image_builder.utils.arn_parser import ARN

NOTIFY_DATA_KEYS = ["revision_commit", "repository_name", "repository_url"]


class Settings:
    channel: str
    workspace: str
    build_arn: str


class Notify:
    reference: str | None
    settings: Settings

    def __init__(
        self,
        send_notifications: bool = True,
        # logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.settings = Settings()
        self.send_notifications = send_notifications
        self.reference = None
        # self.logger = logger

        if self.send_notifications:
            try:
                self.settings.build_arn = os.environ["CODEBUILD_BUILD_ARN"]
                self.slack = WebClient(token=os.environ["SLACK_TOKEN"])
                self.settings.channel = os.environ["SLACK_CHANNEL_ID"]
            except KeyError as e:
                raise ValueError(f"{e} environment variable must be set")

    def _validate_data(self, data):
        if data is None:
            raise ValueError(f"The notification data can't be empty.")

        if not isinstance(data, dict):
            raise ValueError(f"The notification data isn't a valid object.")

        if sorted(NOTIFY_DATA_KEYS) != sorted(data.keys()):
            raise ValueError(
                f"The notification data must include revision_commit, repository_name and repository_url."
            )

    def post_build_progress(self, progress: Progress, text_blocks=None):
        if self.send_notifications:
            self._validate_data(text_blocks)

            message_headline = (
                f"*Building {text_blocks['repository_name']}@"
                f"{text_blocks['revision_commit']}*"
            )
            message_repository = (
                f"*Repository*: <{text_blocks['repository_url']}|"
                f"{text_blocks['repository_name']}>"
            )
            message_revision = (
                f"*Revision*: <{text_blocks['repository_url']}/commit/"
                f"{text_blocks['revision_commit']}|{text_blocks['revision_commit']}>"
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

            try:
                if self.reference is None:
                    response = self.slack.chat_postMessage(
                        channel=os.environ["SLACK_CHANNEL_ID"],
                        blocks=message_blocks,
                        text=f"Building: {text_blocks['repository_name']}@{text_blocks['revision_commit']}",
                        unfurl_links=False,
                        unfurl_media=False,
                    )
                    self.reference = response["ts"]
                else:
                    response = self.slack.chat_update(
                        channel=os.environ["SLACK_CHANNEL_ID"],
                        blocks=message_blocks,
                        ts=self.reference,
                        text=f"Building: {text_blocks['repository_name']}@{text_blocks['revision_commit']}",
                        unfurl_links=False,
                        unfurl_media=False,
                    )
                    self.reference = response["ts"]
            except SlackApiError as e:
                # self.logger.error(f"Slack API Error: {e.response['error']}")
                print(f"Slack API Error: {e.response['error']}", file=sys.stderr)
            except Exception as e:
                # self.logger.error(f"Error sending Slack message: {str(e)}")
                print(f"Error sending Slack message: {str(e)}", file=sys.stderr)

    def post_job_comment(
        self, title: str, message: List[str], send_to_main_channel=False
    ):
        try:
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
        except SlackApiError as e:
            # self.logger.error(f"Slack API Error: {e.response['error']}")
            print(f"Slack API Error: {e.response['error']}", file=sys.stderr)
        except Exception as e:
            # self.logger.error(f"Error sending Slack message: {str(e)}")
            print(f"Error sending Slack message: {str(e)}", file=sys.stderr)

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
