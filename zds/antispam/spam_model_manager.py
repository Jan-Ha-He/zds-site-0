import logging
import os

import joblib
from django.conf import settings
from factory.fuzzy import FuzzyText
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.svm import LinearSVC

from zds.member.models import Profile


class SpamModelManager:
    def __init__(self, model_file=None):
        self.model_file = model_file or os.path.join(settings.ANTISPAM_PATH, settings.ANTISPAM_MODEL_FILE)
        self.clf = None
        self.count_vect = None
        self.tfidf_transformer = None
        self.logger = logging.getLogger(__name__)

    def ensure_directory_exists(self):
        directory = os.path.dirname(self.model_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"Created directory: {directory}")

    def prepare_training_data(self):
        """
        Prepare training data from existing profiles or generate fake data if insufficient.
        """
        bios = []
        can_read = []

        profiles = Profile.objects.all()

        if profiles.count() < 100:
            # Generate fake data for testing
            spam_profiles = [f"spam {FuzzyText(prefix='spammy').fuzz()} buy now free !!" for _ in range(50)]
            non_spam_profiles = [f"correct {FuzzyText(prefix='normal').fuzz()} about ..." for _ in range(50)]

            bios = spam_profiles + non_spam_profiles
            can_read = [0] * len(spam_profiles) + [1] * len(non_spam_profiles)
        else:
            for profile in profiles:
                if not profile.biography:
                    continue
                bios.append(profile.biography)
                can_read.append(1 if profile.can_read else 0)

        return bios, can_read

    def train(self):
        """
        Prepare data, train the spam filter model, and save it to a file.
        """
        self.logger.info("Starting training of the spam filter model...")

        # Ensure the directory exists
        self.ensure_directory_exists()

        # Prepare training data
        bio_train, can_read_train = self.prepare_training_data()

        # Train the model
        self.count_vect = CountVectorizer()
        X_train_counts = self.count_vect.fit_transform(bio_train)

        self.tfidf_transformer = TfidfTransformer()
        X_train_tfidf = self.tfidf_transformer.fit_transform(X_train_counts)

        self.clf = LinearSVC(max_iter=5000, loss="hinge", dual="auto")
        self.clf.fit(X_train_tfidf, can_read_train)

        self.logger.info("Training completed.")

        # Save the model
        joblib.dump((self.clf, self.count_vect, self.tfidf_transformer), self.model_file)
        self.logger.info(f"Model saved to {self.model_file}")

    def load_model(self):
        """
        Load the model from a file if it exists.
        """
        if os.path.exists(self.model_file):
            self.clf, self.count_vect, self.tfidf_transformer = joblib.load(self.model_file)
            self.logger.info(f"Model loaded from {self.model_file}")
        else:
            self.logger.info(f"Model file '{self.model_file}' does not exist. Skipping loading step.")

    def predict(self, biographies):
        """
        Predict whether the given biographies are spam or not.
        """
        if not self.clf or not self.count_vect or not self.tfidf_transformer:
            self.logger.error("Model not loaded.")
            self.train()
        X_new_counts = self.count_vect.transform(biographies)
        X_new_tfidf = self.tfidf_transformer.transform(X_new_counts)
        return self.clf.predict(X_new_tfidf)
