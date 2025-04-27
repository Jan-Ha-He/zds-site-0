import logging
import os

import joblib
from django.conf import settings
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.svm import LinearSVC


class SpamModelManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_mapping = {
            "PROFILE": "profile_spam_model.pkl",
            "FORUM": "forum_spam_model.pkl",
            "CONTENT": "content_spam_model.pkl",
        }
        self.models = {}

    def ensure_directory_exists(self, model_file):
        directory = os.path.dirname(model_file)
        if not directory:
            raise ValueError("The directory for the model file is not defined.")
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"Created directory: {directory}")

    def prepare_training_data(self, content_type):
        """
        Prepare training data for the given content type.
        """
        # Implement logic to fetch or generate training data based on content_type
        bios = ["example spam text", "example non-spam text"]
        labels = [0, 1]  # 0 for spam, 1 for non-spam
        return bios, labels

    def train(self, content_type):
        """
        Train the model for the given content type and save it to a file.
        """
        self.logger.info(f"Starting training for content type: {content_type}")

        model_file = os.path.join(settings.ANTISPAM_PATH, self.model_mapping[content_type])
        self.ensure_directory_exists(model_file)

        # Prepare training data
        data, labels = self.prepare_training_data(content_type)

        # Train the model
        count_vect = CountVectorizer()
        X_train_counts = count_vect.fit_transform(data)

        tfidf_transformer = TfidfTransformer()
        X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)

        clf = LinearSVC(max_iter=5000, loss="hinge", dual="auto")
        clf.fit(X_train_tfidf, labels)

        # Save the model
        joblib.dump((clf, count_vect, tfidf_transformer), model_file)
        self.logger.info(f"Model for {content_type} saved to {model_file}")

        # Store the model in memory
        self.models[content_type] = (clf, count_vect, tfidf_transformer)

    def load_model(self, content_type):
        """
        Load the model for the given content type from a file.
        """
        model_file = os.path.join(settings.ANTISPAM_PATH, self.model_mapping[content_type])
        if os.path.exists(model_file):
            self.models[content_type] = joblib.load(model_file)
            self.logger.info(f"Model for {content_type} loaded from {model_file}")
        else:
            self.logger.warning(f"Model file for {content_type} does not exist. Training a new model.")
            self.train(content_type)

    def predict(self, content_type, texts):
        """
        Predict whether the given texts are spam or not for the specified content type.
        """
        if content_type not in self.models:
            self.load_model(content_type)

        clf, count_vect, tfidf_transformer = self.models[content_type]
        X_new_counts = count_vect.transform(texts)
        X_new_tfidf = tfidf_transformer.transform(X_new_counts)
        return clf.predict(X_new_tfidf)
