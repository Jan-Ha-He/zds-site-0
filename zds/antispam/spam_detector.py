import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from zds.antispam.spam_model_manager import SpamModelManager
from zds.member.models import Profile
from zds.utils.models import Alert


class SpamDetector:
    def __init__(self, model_file="spam_filter_model.pkl"):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)
        self.model_manager = SpamModelManager(model_file)
        self.model_manager.load_model()

    def check_profile(self, profile):
        biography = profile.biography

        if not biography:
            self.logger.info("∅  %s has no biography" % profile.user.username)
            return False

        if self.model_manager.predict([biography])[0] == 0:
            self.logger.info("✘  %s's biography looks like spam" % profile.user.username)
            self.send_alert(None, profile.user.username)
        else:
            self.logger.info("✔️  %s's biography doesn't look like spam" % profile.user.username)

        self.logger.info(f"Profile checked: {profile.user.username}\n" f"Biography: {profile.biography}\n" f"{'='*50}")

    def send_alert(self, website, username):
        """
        Create an alert for a spam-suspect user
        """
        try:
            profile = Profile.objects.get(user__username=username)

            message = _("Spam")

            Alert.objects.create(
                author=User.objects.get(username="bot"),
                profile=profile,
                scope="PROFILE",
                text=message,
                pubdate=datetime.now(),
            )

            self.logger.info(f"Spam-Alert for {username} created")
            return True

        except Exception as e:
            self.logger.error(f"Error on creation of spam report for {username}: {str(e)}")
            return False
