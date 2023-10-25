import os
import unittest
from test.doubles.slack import WebClient
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from parameterized import parameterized
from slack_sdk.models import blocks

from image_builder.notify import Notify
from image_builder.progress import Progress


@patch("builtins.round", return_value=15)
@patch("image_builder.notify.WebClient", return_value=WebClient("slack-token"))
class TestNotify(unittest.TestCase):
    def setUp(self):
        os.environ["SLACK_TOKEN"] = "slack-token"
        os.environ["SLACK_CHANNEL_ID"] = "channel-id"
        os.environ["CODEBUILD_BUILD_ARN"] = (
            "arn:aws:codebuild:region:000000000000:build/project" ":example-build-id"
        )
        self.codebase = MagicMock()
        self.codebase.revision.commit = "commit-sha"
        self.codebase.revision.get_repository_name.return_value = "org/repo"
        self.codebase.revision.get_repository_url.return_value = (
            "https://github.com/org/repo"
        )

    @parameterized.expand(
        [
            ("SLACK_TOKEN",),
            ("SLACK_CHANNEL_ID",),
            ("CODEBUILD_BUILD_ARN",),
        ]
    )
    def test_raises_error_when_environment_not_set(
        self, webclient, time, environment_variable
    ):
        del os.environ[environment_variable]
        with pytest.raises(ValueError) as e:
            Notify(self.codebase)
        self.assertEqual(
            f"'{environment_variable}' environment variable must be set", str(e.value)
        )

    def test_getting_build_url(self, webclient, time):
        notify = Notify(self.codebase)
        self.assertEqual(
            notify.get_build_url(),
            "https://region.console.aws.amazon.com/codesuite/codebuild/000000000000"
            "/projects/project/build/project%3Aexample-build-id",
        )

    def test_sending_progress_updates(self, webclient, time):
        notify = Notify(self.codebase)
        progress = Progress()
        notify.post_progress(progress)
        notify.post_progress(progress)
        notify.slack.chat_postMessage.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )
        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            ts="first-message",
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )
        notify.post_progress(progress)
        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            ts="updated-message",
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_sending_all_build_stages_successful(self, webclient, time):
        notify = Notify(self.codebase)
        progress = Progress()

        progress.current_phase_running()
        notify.post_progress(progress)

        notify.slack.chat_postMessage.assert_called_with(
            channel="channel-id",
            blocks=[
                ANY,
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Repository*: <https://github.com/org/repo|org/repo>",
                        ),
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Revision*: <https://github.com/org/repo/commit/commit-sha|commit-sha>",
                        ),
                    ]
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*setup*: running :hourglass_flowing_sand:"
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*build*: pending :large_blue_circle:"
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*publish*: pending :large_blue_circle:"
                    )
                ),
                ANY,
            ],
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set build to running
        progress.current_phase_success()
        progress.set_current_phase("build")
        progress.current_phase_running()
        notify.post_progress(progress)

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="first-message",
            blocks=[
                ANY,
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Repository*: <https://github.com/org/repo|org/repo>",
                        ),
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Revision*: <https://github.com/org/repo/commit/commit-sha|commit-sha>",
                        ),
                    ]
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*setup*: success :large_green_circle: - took 15 seconds",
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*build*: running :hourglass_flowing_sand:"
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*publish*: pending :large_blue_circle:"
                    )
                ),
                ANY,
            ],
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set publish to running
        progress.current_phase_success()
        progress.set_current_phase("publish")
        progress.current_phase_running()
        notify.post_progress(progress)

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="updated-message",
            blocks=[
                ANY,
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Repository*: <https://github.com/org/repo|org/repo>",
                        ),
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Revision*: <https://github.com/org/repo/commit/commit-sha|commit-sha>",
                        ),
                    ]
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*setup*: success :large_green_circle: - took 15 seconds",
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*build*: success :large_green_circle: - took 15 seconds",
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*publish*: running :hourglass_flowing_sand:",
                    )
                ),
                ANY,
            ],
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set state to done
        progress.current_phase_success()
        notify.post_progress(progress)

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="updated-message",
            blocks=[
                ANY,
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Repository*: <https://github.com/org/repo|org/repo>",
                        ),
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Revision*: <https://github.com/org/repo/commit/commit-sha|commit-sha>",
                        ),
                    ]
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*setup*: success :large_green_circle: - took 15 seconds",
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*build*: success :large_green_circle: - took 15 seconds",
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*publish*: success :large_green_circle: - took 15 seconds",
                    )
                ),
                ANY,
            ],
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_sending_a_failure_update(self, webclient, time):
        notify = Notify(self.codebase)
        progress = Progress()

        progress.current_phase_running()
        progress.current_phase_failure()
        notify.post_progress(progress)

        notify.slack.chat_postMessage.assert_called_with(
            channel="channel-id",
            blocks=[
                ANY,
                blocks.ContextBlock(
                    elements=[
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Repository*: <https://github.com/org/repo|org/repo>",
                        ),
                        blocks.TextObject(
                            type="mrkdwn",
                            text=f"*Revision*: <https://github.com/org/repo/commit/commit-sha|commit-sha>",
                        ),
                    ]
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn",
                        text=f"*setup*: failure :red_circle: - took 15 seconds",
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*build*: pending :large_blue_circle:"
                    )
                ),
                blocks.SectionBlock(
                    text=blocks.TextObject(
                        type="mrkdwn", text=f"*publish*: pending :large_blue_circle:"
                    )
                ),
                ANY,
            ],
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )
