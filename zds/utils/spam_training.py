from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.svm import LinearSVC
from pprint import pprint
from zds.member.models import Profile

# Data importation
_bio = ["Je suis un vrai utilisateur", "Gagner d'Argent"]
_can_read = [0, 1]

profiles = Profile.objects.all()

for profile in profiles:
    if not profile.biography:
        continue
    _bio.append(profile.biography)
    _can_read.append(1 if profile.can_read else 0)

_limit = int(round(len(_bio) * 0.8))

bio_train = _bio[:_limit]
can_read_train = _can_read[:_limit]

bio_test = _bio[_limit:]
can_read_test = _can_read[_limit:]

# Transformation text->number (text preprocessing, tokenizing and filtering of stopwords)

count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(bio_train)

# Frequency calculation

tfidf_transformer = TfidfTransformer()
X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)

# Classifier training

clf = LinearSVC(max_iter=5000, loss="hinge", dual="auto")
clf.fit(X_train_tfidf, can_read_train)

# Prediction of test data

X_new_counts = count_vect.transform(bio_test)
X_new_tfidf = tfidf_transformer.transform(X_new_counts)

predicted = clf.predict(X_new_tfidf)

if __name__ == "__main__":
    average = 0
    confusions = {}
    for real, pred in zip(can_read_test, predicted):
        if real == pred:
            average += 1

        elem = f"real {real} => pred {pred}"

        if not confusions.get(elem, False):
            confusions[elem] = [0, ""]

        confusions[elem][0] += 1

    for elem in confusions:
        confusions[elem][1] = f"{round(confusions[elem][0]/len(can_read_test)*100)} %"

    print("\n", round(average / len(can_read_test) * 100, 2), "%\n\n")

    pprint(confusions)
