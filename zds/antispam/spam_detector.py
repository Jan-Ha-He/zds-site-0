import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from zds.member.models import Profile
from zds.utils.models import Alert

from .spam_training import clf, count_vect, tfidf_transformer


class SpamDetector:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)

    def check_profile(self, profile):
        biography = profile.biography

        if not biography:
            self.logger.info("∅  %s has no biography" % profile.user.username)
            return False

        if self.check(biography) == 0:
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

    def check(self, biography):
        x_new_counts = count_vect.transform([biography])
        x_new_tfidf = tfidf_transformer.transform(x_new_counts)
        return clf.predict(x_new_tfidf)[0]
