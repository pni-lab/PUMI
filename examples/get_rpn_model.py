from PUMI.utils import rpn_model
import numpy as np


clf = rpn_model(file='../data_in/rpn_model.json')  # Load scikit-learn model
np.random.seed(42)  # Set seed for random number generator for reproducibility
X = np.random.rand(7503, 7503)  # Generate random matrix of size 7503x7503
output = clf.predict(X)  # Let the model work
print(np.sum(output))  # The sum of the output should be '-33289.640430609696'
