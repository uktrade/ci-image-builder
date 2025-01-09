import os
import unittest
from test.doubles.slack import WebClient
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from parameterized import parameterized
from slack_sdk.errors import SlackApiError
from slack_sdk.models import blocks

from image_builder.notify import Notify
from image_builder.progress import Progress


@patch("builtins.round", return_value=15)
@patch("image_builder.notify.WebClient", return_value=WebClient("slack-token"))
class TestNotify(unittest.TestCase):
    def setUp(self):
        os.environ["SLACK_TOKEN"] = "slack-token"
        os.environ["SLACK_CHANNEL_ID"] = "channel-id"
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"
        self.codebase = MagicMock()
        self.codebase.get_notify_attrs.return_value = {
            "repository_name": "org/repo",
            "revision_commit": "commit-sha",
            "repository_url": "https://github.com/org/repo",
        }
        self.extras = {
            "repository_name": "org/repo-extra",
            "revision_commit": "commit-sha-extra",
            "repository_url": "https://github.com/org/repo-extra",
        }

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
            Notify(True)
        self.assertEqual(
            f"'{environment_variable}' environment variable must be set", str(e.value)
        )

    def test_getting_build_url(self, webclient, time):
        notify = Notify(True)
        self.assertEqual(
            notify.get_build_url(),
            "https://region.console.aws.amazon.com/codesuite/codebuild/000000000000"
            "/projects/project/build/project%3Aexample-build-id",
        )

    def test_sending_progress_updates(self, webclient, time):
        notify = Notify(True)
        progress = Progress()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())
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
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())
        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            ts="updated-message",
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_sending_progress_updates_non_codebase_data(self, webclient, time):
        notify = Notify(True)
        progress = Progress()
        notify.post_build_progress(progress, self.extras)
        notify.post_build_progress(progress, self.extras)
        notify.slack.chat_postMessage.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            text="Building: org/repo-extra@commit-sha-extra",
            unfurl_links=False,
            unfurl_media=False,
        )
        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            ts="first-message",
            text="Building: org/repo-extra@commit-sha-extra",
            unfurl_links=False,
            unfurl_media=False,
        )
        notify.post_build_progress(progress, self.extras)
        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            blocks=ANY,
            ts="updated-message",
            text="Building: org/repo-extra@commit-sha-extra",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_sending_progress_updates_when_notifications_off(self, webclient, time):
        notify = Notify(False)
        progress = Progress()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())
        self.assertFalse(hasattr(notify, "slack"))

    def test_sending_all_build_stages_successful(self, webclient, time):
        notify = Notify()
        progress = Progress()

        progress.current_phase_running()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        notify.slack.chat_postMessage.assert_called_with(
            channel="channel-id",
            blocks=get_expected_message_blocks(),
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set build to running
        progress.current_phase_success()
        progress.set_current_phase("build")
        progress.current_phase_running()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="first-message",
            blocks=get_expected_message_blocks(setup="success", build="running"),
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set publish to running
        progress.current_phase_success()
        progress.set_current_phase("publish")
        progress.current_phase_running()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="updated-message",
            blocks=get_expected_message_blocks(
                setup="success", build="success", publish="running"
            ),
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set deploy to running
        progress.current_phase_success()
        progress.set_current_phase("deploy")
        progress.current_phase_running()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="updated-message",
            blocks=get_expected_message_blocks(
                setup="success", build="success", publish="success", deploy="running"
            ),
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

        # set state to done
        progress.current_phase_success()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        notify.slack.chat_update.assert_called_with(
            channel="channel-id",
            ts="updated-message",
            blocks=get_expected_message_blocks(
                setup="success", build="success", publish="success", deploy="success"
            ),
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_sending_a_failure_update(self, webclient, time):
        notify = Notify()
        progress = Progress()

        progress.current_phase_running()
        progress.current_phase_failure()
        notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        notify.slack.chat_postMessage.assert_called_with(
            channel="channel-id",
            blocks=get_expected_message_blocks("failure"),
            text="Building: org/repo@commit-sha",
            unfurl_links=False,
            unfurl_media=False,
        )

    def test_sending_progress_updates_missing_data(self, webclient, time):
        notify = Notify(True)
        progress = Progress()

        with pytest.raises(ValueError) as e:
            notify.post_build_progress(progress, None)

        self.assertEqual(f"The notification data can't be empty.", str(e.value))

    def test_sending_progress_updates_invalid_type(self, webclient, time):
        notify = Notify(True)
        progress = Progress()

        with pytest.raises(ValueError) as e:
            notify.post_build_progress(progress, "Invalid")

        self.assertEqual(f"The notification data isn't a valid object.", str(e.value))

    def test_sending_progress_updates_invalid_data(self, webclient, time):
        notify = Notify(True)
        progress = Progress()

        with pytest.raises(ValueError) as e:
            notify.post_build_progress(progress, {"invalid_key": "test"})

        self.assertEqual(
            f"The notification data must include revision_commit, repository_name and repository_url.",
            str(e.value),
        )

    def test_slack_api_error_on_chat_post_message(self, webclient, time):
        notify = Notify(True)
        progress = Progress()

        notify.slack.chat_postMessage.side_effect = SlackApiError(
            message="invalid_arguments",
            response={"ok": False, "error": "invalid_arguments"},
        )

        with self.assertLogs(logger="image_builder.notify") as log:
            notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        self.assertEqual(
            log.records[0].getMessage(), "Slack API Error: invalid_arguments"
        )

    def test_slack_api_error_on_chat_update(self, webclient, time):
        notify = Notify(True)
        progress = Progress()

        notify.reference = "mock-timestamp"

        notify.slack.chat_update.side_effect = SlackApiError(
            message="message_not_found",
            response={"ok": False, "error": "message_not_found"},
        )

        with self.assertLogs(logger="image_builder.notify") as log:
            notify.post_build_progress(progress, self.codebase.get_notify_attrs())

        self.assertEqual(
            log.records[0].getMessage(), "Slack API Error: message_not_found"
        )


def test_exception_on_chat_post_message():
    mock_logger = MagicMock()
    notify = Notify(True, logger=mock_logger)
    notify.slack = WebClient("slack-token")
    progress = Progress()

    original_environ = os.environ.copy()
    del os.environ["SLACK_CHANNEL_ID"]

    notify.post_build_progress(
        progress,
        {
            "repository_name": "org/repo",
            "revision_commit": "commit-sha",
            "repository_url": "https://github.com/org/repo",
        },
    )
    os.environ.update(original_environ)

    mock_logger.error.assert_called_once_with(
        "Error sending Slack message: 'SLACK_CHANNEL_ID'"
    )


def test_exception_on_chat_update_message():
    mock_logger = MagicMock()
    notify = Notify(True, logger=mock_logger)
    notify.slack = WebClient("slack-token")
    progress = Progress()

    notify.reference = "mock-timestamp"

    notify.slack.chat_update.side_effect = Exception("Something went wrong")

    notify.post_build_progress(
        progress,
        {
            "repository_name": "org/repo",
            "revision_commit": "commit-sha",
            "repository_url": "https://github.com/org/repo",
        },
    )

    mock_logger.error.assert_called_once_with(
        "Error sending Slack message: Something went wrong"
    )


def get_expected_message_blocks(
    setup="running", build="pending", publish="pending", deploy="pending"
):
    phase_messages = {
        "pending": "Pending :large_blue_circle:",
        "running": "Running :hourglass_flowing_sand:",
        "success": "Success :large_green_circle: (15 s)",
        "failure": "Failure :red_circle: (15 s)",
    }

    return [
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
                blocks.TextObject(
                    type="mrkdwn",
                    text=f"<https://region.console.aws.amazon.com/codesuite/codebuild/000000000000"
                    f"/projects/project/build/project%3Aexample-build-id|Build Logs>",
                ),
            ]
        ),
        blocks.ContextBlock(
            elements=[
                blocks.TextObject(
                    type="mrkdwn",
                    text=f"*Setup*: {phase_messages[setup]}",
                ),
                blocks.TextObject(
                    type="mrkdwn",
                    text=f"*Build*: {phase_messages[build]}",
                ),
                blocks.TextObject(
                    type="mrkdwn",
                    text=f"*Publish*: {phase_messages[publish]}",
                ),
                blocks.TextObject(
                    type="mrkdwn",
                    text=f"*Deploy*: {phase_messages[deploy]}",
                ),
            ]
        ),
    ]
