import logging
import os

import joblib
from factory.fuzzy import FuzzyText
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.svm import LinearSVC

from zds.member.models import Profile


class SpamModelManager:
    def __init__(self, model_file="spam_filter_model.pkl"):
        self.model_file = model_file
        self.clf = None
        self.count_vect = None
        self.tfidf_transformer = None
        self.logger = logging.getLogger(__name__)

    def train(self, bio_train, can_read_train):
        """
        Train the spam filter model with the given data.
        """
        self.logger.info("Training the spam filter model...")
        self.count_vect = CountVectorizer()
        X_train_counts = self.count_vect.fit_transform(bio_train)

        self.tfidf_transformer = TfidfTransformer()
        X_train_tfidf = self.tfidf_transformer.fit_transform(X_train_counts)

        self.clf = LinearSVC(max_iter=5000, loss="hinge", dual="auto")
        self.clf.fit(X_train_tfidf, can_read_train)
        self.logger.info("Training completed.")

    def save_model(self):
        """
        Save the trained model to a file.
        """
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
            raise ValueError("Model is not loaded or trained.")
        X_new_counts = self.count_vect.transform(biographies)
        X_new_tfidf = self.tfidf_transformer.transform(X_new_counts)
        return self.clf.predict(X_new_tfidf)

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

    def retrain(self):
        """
        Retrain the spam filter model with new data.
        """
        self.logger.info("Retraining the spam filter model...")
        bio_train, can_read_train = self.prepare_training_data()
        self.train(bio_train, can_read_train)
        self.save_model()
        self.logger.info("Retraining completed.")
