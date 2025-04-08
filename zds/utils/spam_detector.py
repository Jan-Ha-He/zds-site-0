import logging
from datetime import datetime
import os
from django.conf import settings
from .spam_training import count_vect, tfidf_transformer, clf
from django.utils.translation import gettext_lazy as _
from zds.utils.models import Alert
from zds.member.models import Profile
from django.contrib.auth.models import User


class SpamDetector:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def check_profile(self, profile):
        """
        Check if a profile is a spammer
        """
        spam_count = Profile.objects.filter(can_read=0).count()
        non_spam_count = Profile.objects.filter(can_read=1).count()

        if spam_count < 5 or non_spam_count < 5:
            self.logger.info(
                "Not enough data to perform spam checks (spam: %d, non-spam: %d)", spam_count, non_spam_count
            )
            return False

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

    def check(self, biography):
        X_new_counts = count_vect.transform([biography])
        X_new_tfidf = tfidf_transformer.transform(X_new_counts)
        return clf.predict(X_new_tfidf)[0]

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
