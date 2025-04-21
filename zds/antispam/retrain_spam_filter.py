from zds.antispam.spam_model_manager import SpamModelManager

if __name__ == "__main__":
    model_manager = SpamModelManager()
    model_manager.retrain()
