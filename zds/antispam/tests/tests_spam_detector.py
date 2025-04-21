from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from zds.antispam.spam_detector import SpamDetector
from zds.member.models import Profile


class SpamDetectorTestCase(TestCase):
    def setUp(self):
        self.spam_detector = SpamDetector()
        self.bot_user = User.objects.create_user(username="bot", password="password")

        self.user1 = User.objects.create_user(username="user_no_bio", password="password")
        self.profile1 = Profile.objects.create(user=self.user1, biography="")

        self.user2 = User.objects.create_user(username="user_spam", password="password")
        self.profile2 = Profile.objects.create(user=self.user2, biography="Buy cheap products now!")

        self.user3 = User.objects.create_user(username="user_clean", password="password")
        self.profile3 = Profile.objects.create(user=self.user3, biography="I love programming and open-source.")

    @patch("zds.antispam.spam_model_manager.SpamModelManager.predict", return_value=[0])
    def test_check_profile_spam(self, mock_predict):
        """Test that a spam profile triggers an alert."""
        with patch.object(self.spam_detector, "send_alert") as mock_send_alert:
            self.spam_detector.check_profile(self.profile2)
            mock_predict.assert_called_once_with(["Buy cheap products now!"])
            mock_send_alert.assert_called_once_with(None, self.user2.username)

    @patch("zds.antispam.spam_model_manager.SpamModelManager.predict", return_value=[1])
    def test_check_profile_clean(self, mock_predict):
        """Test that a clean profile does not trigger an alert."""
        with patch.object(self.spam_detector, "send_alert") as mock_send_alert:
            self.spam_detector.check_profile(self.profile3)
            mock_predict.assert_called_once_with(["I love programming and open-source."])
            mock_send_alert.assert_not_called()
