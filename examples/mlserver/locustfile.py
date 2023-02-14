from locust import FastHttpUser, task
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
X_train, X_test, y_train, y_test = train_test_split(data, digits.target, test_size=0.5, shuffle=False)

x_0 = X_test[0:1]
inference_request = {
    "inputs": [
        {
            "name": "predict",
            "shape": x_0.shape,
            "datatype": "FP32",
            "data": x_0.tolist(),
        }
    ]
}


class HelloWorldUser(FastHttpUser):
    @task
    def predict(self):
        self.client.post("/v2/models/mnist-svm/versions/v0.0.1/infer", json=inference_request)
