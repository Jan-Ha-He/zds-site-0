from unittest import TestCase
from unittest.mock import MagicMock, patch

from zds.antispam.spam_model_manager import SpamModelManager


class SpamModelManagerTestCase(TestCase):
    def setUp(self):
        """Set up test users and spam manager."""
        self.model_manager = SpamModelManager()

    @patch("zds.antispam.spam_model_manager.joblib.dump")
    def test_save_model(self, mock_dump):
        """Test that the model is saved correctly."""
        self.model_manager.clf = MagicMock()
        self.model_manager.count_vect = MagicMock()
        self.model_manager.tfidf_transformer = MagicMock()
        self.model_manager.save_model()
        mock_dump.assert_called_once()

    @patch("zds.antispam.spam_model_manager.joblib.load", return_value=(MagicMock(), MagicMock(), MagicMock()))
    @patch("zds.antispam.spam_model_manager.os.path.exists", return_value=True)
    def test_load_model(self, mock_exists, mock_load):
        """Test that the model is loaded correctly if the file exists."""
        self.model_manager.load_model()
        mock_load.assert_called_once_with(self.model_manager.model_file)
        self.assertIsNotNone(self.model_manager.clf)
        self.assertIsNotNone(self.model_manager.count_vect)
        self.assertIsNotNone(self.model_manager.tfidf_transformer)

    @patch("zds.antispam.spam_model_manager.os.path.exists", return_value=False)
    def test_load_model_file_not_exist(self, mock_exists):
        """Test that loading is skipped if the file does not exist."""
        with self.assertLogs("zds.antispam.spam_model_manager", level="INFO") as log:
            self.model_manager.load_model()
            self.assertIn("Model file 'spam_filter_model.pkl' does not exist", log.output[0])

    @patch("zds.antispam.spam_model_manager.CountVectorizer.fit_transform")
    @patch("zds.antispam.spam_model_manager.TfidfTransformer.fit_transform")
    @patch("zds.antispam.spam_model_manager.LinearSVC.fit")
    def test_train_model(self, mock_fit, mock_tfidf, mock_count_vect):
        """Test that the model is trained correctly."""
        bio_train = ["spam text", "clean text"]
        can_read_train = [0, 1]
        self.model_manager.train(bio_train, can_read_train)
        mock_count_vect.assert_called_once()
        mock_tfidf.assert_called_once()
        mock_fit.assert_called_once()
