from lightning import LightningApp, LightningFlow, LightningWork
from lightning.app.storage import Path

from lightning_serve.locust import Locust
from lightning_serve.mlserver import MLServer


class TrainWork(LightningWork):
    def __init__(self):
        super().__init__()
        self.best_model_path = None

    def run(self):
        import joblib
        from sklearn import datasets, svm
        from sklearn.model_selection import train_test_split

        # The digits dataset
        digits = datasets.load_digits()

        # To apply a classifier on this data, we need to flatten the image, to
        # turn the data in a (samples, feature) matrix:
        n_samples = len(digits.images)
        data = digits.images.reshape((n_samples, -1))

        # Create a classifier: a support vector classifier
        classifier = svm.SVC(gamma=0.001)

        # Split data into train and test subsets
        X_train, X_test, y_train, y_test = train_test_split(
            data, digits.target, test_size=0.5, shuffle=False
        )

        # We learn the digits on the first half of the digits
        classifier.fit(X_train, y_train)

        model_file_name = "mnist-svm.joblib"
        joblib.dump(classifier, model_file_name)
        self.best_model_path = Path("mnist-svm.joblib")


class TrainAndDeploy(LightningFlow):
    def __init__(self):
        super().__init__()
        self.train = TrainWork()
        self.serve = MLServer(
            "mnist-svm", "mlserver_sklearn.SKLearnModel", workers=4, parallel=True
        )
        self.locust = Locust(100)

    def run(self):
        self.train.run()
        self.serve.run(self.train.best_model_path)
        if self.serve.url != "":
            self.locust.run(self.serve.url)

    def configure_layout(self):
        return [
            {"name": "Server", "content": self.serve.url + "/docs"},
            {"name": "Load Testing", "content": self.locust},
        ]


app = LightningApp(TrainAndDeploy())
