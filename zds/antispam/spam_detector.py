import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from zds.antispam.spam_fields import spam_fields
from zds.antispam.spam_model_manager import SpamModelManager
from zds.utils.models import Alert


class SpamDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_manager = SpamModelManager()

    def check_text(self, text, content_type):
        """
        Check if a given text is spam for the specified content type.
        """
        if not text:
            return False

        try:
            prediction = self.model_manager.predict(content_type, [text])[0]
            if prediction == 0:  # 0 indicates spam
                self.logger.info(f"✘ Text looks like spam: {text[:30]}...")
                return True
            else:
                self.logger.info(f"✔️ Text doesn't look like spam.")
                return False
        except Exception as e:
            self.logger.error(f"Error during spam detection: {e}")
            return False

    def send_alert(self, instance, field_name):
        """
        Create an alert for a spam-suspect field with detailed context.
        """
        try:
            # Find the spam field configuration for the instance
            field_config = next(
                (
                    config
                    for config in spam_fields
                    if isinstance(instance, config["model"]) and config["field"] == field_name
                ),
                None,
            )
            if not field_config:
                self.logger.error(f"No spam field configuration found for {type(instance).__name__}.{field_name}")
                return

            # Extract scope and instance info
            scope = field_config["scope"]
            instance_info = field_config["get_instance_info"](instance)

            # Map scope to the correct Alert model field
            alert_kwargs = {
                "author": User.objects.get(username="antispam"),
                "scope": scope,
                "text": _(f"Potential spam detected in {instance_info}, field '{field_name}'."),
                "pubdate": datetime.now(),
            }
            if scope == "PROFILE":
                alert_kwargs["profile"] = instance
            elif scope == "FORUM":
                alert_kwargs["comment"] = instance
            elif scope == "CONTENT":
                alert_kwargs["content"] = instance
            else:
                self.logger.error(f"Unsupported scope '{scope}' for alert creation.")
                return

            # Create the alert
            Alert.objects.create(**alert_kwargs)
            self.logger.info(f"Spam-Alert for {instance_info}, field '{field_name}' created.")
        except User.DoesNotExist:
            self.logger.error("The 'antispam' user does not exist. Please create this user.")
        except Exception as e:
            self.logger.error(f"Failed to create spam alert: {e}")
