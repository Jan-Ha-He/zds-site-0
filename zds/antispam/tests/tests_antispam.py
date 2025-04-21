from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from zds.antispam.spam_detector import SpamDetector
from zds.member.models import Profile


class SpamDetectorTestCase(TestCase):

    def setUp(self):
        """Set up test users and spam detector."""
        self.spam_detector = SpamDetector()
        self.bot_user = User.objects.create_user(username="bot", password="password")

        self.user1 = User.objects.create_user(username="user_no_bio", password="password")
        self.profile1 = Profile.objects.create(user=self.user1, biography="")

        self.user2 = User.objects.create_user(username="user_spam", password="password")
        self.profile2 = Profile.objects.create(user=self.user2, biography="Buy cheap products now!")

        self.user3 = User.objects.create_user(username="user_clean", password="password")
        self.profile3 = Profile.objects.create(user=self.user3, biography="I love programming and open-source.")

    @patch("zds.antispam.spam_detector.SpamDetector.send_alert")
    def test_check_profile_no_bio(self, mock_send_alert):
        """User with no biography should not trigger an alert."""
        with self.assertLogs("zds.antispam.spam_detector", level="INFO") as log:
            self.spam_detector.check_profile(self.profile1)
            mock_send_alert.assert_not_called()
            self.assertIn("∅  user_no_bio has no biography", log.output[0])

    @patch("zds.antispam.spam_detector.SpamDetector.send_alert", return_value=True)
    @patch("zds.antispam.spam_detector.SpamDetector.check", return_value=0)
    def test_check_profile_spam(self, mock_check, mock_send_alert):
        """User with spam biography should trigger an alert."""
        with self.assertLogs("zds.antispam.spam_detector", level="INFO") as log:
            self.spam_detector.check_profile(self.profile2)
            mock_send_alert.assert_called_once_with(None, "user_spam")
            self.assertIn("✘  user_spam's biography looks like spam", log.output[0])

    @patch("zds.antispam.spam_detector.SpamDetector.send_alert")
    @patch("zds.antispam.spam_detector.SpamDetector.check", return_value=1)
    def test_check_profile_clean(self, mock_check, mock_send_alert):
        """User with a clean biography should not trigger an alert."""
        with self.assertLogs("zds.antispam.spam_detector", level="INFO") as log:
            self.spam_detector.check_profile(self.profile3)
            mock_send_alert.assert_not_called()
            self.assertIn("✔️  user_clean's biography doesn't look like spam", log.output[0])

    @patch("zds.antispam.spam_detector.SpamDetector.check", return_value=0)
    def test_check_function_spam(self, mock_check):
        """check function should correctly classify spam."""
        result = self.spam_detector.check("Buy cheap products now!")
        self.assertEqual(result, 0)

    @patch("zds.antispam.spam_detector.SpamDetector.check", return_value=1)
    def test_check_function_clean(self, mock_check):
        """check function should correctly classify non-spam."""
        result = self.spam_detector.check("I love programming and open-source.")
        self.assertEqual(result, 1)

    @patch("zds.antispam.spam_detector.SpamDetector.send_alert", return_value=True)
    @patch("zds.antispam.spam_detector.SpamDetector.check", return_value=0)
    def test_already_reported_user(self, mock_check, mock_send_alert):
        """Test that spam detection works without reported_users attribute."""
        self.spam_detector.check_profile(self.profile2)
        mock_send_alert.assert_called_once()
