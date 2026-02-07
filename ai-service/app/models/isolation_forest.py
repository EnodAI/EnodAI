import joblib
import numpy as np
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class IsolationForestWrapper:
    def __init__(self, model_path='models/isolation_forest.joblib'):
        self.model = IsolationForest(
            contamination=0.1,
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.is_fitted = False

    def train(self, data: list):
        """
        Train the model with new data.
        Data should be a list of numerical values.
        """
        if not data:
            # Create dummy data for initialization if empty
            data = np.random.normal(loc=50, scale=10, size=1000).reshape(-1, 1)
        else:
            data = np.array(data).reshape(-1, 1)

        self.scaler.fit(data)
        X_scaled = self.scaler.transform(data)
        
        self.model.fit(X_scaled)
        self.is_fitted = True
        self.save()
        print("Model trained and saved.")

    def predict(self, X):
        """
        Predict if values are anomalies.
        Returns array where -1 is anomaly, 1 is normal.
        """
        if not self.is_fitted:
            # If not trained, treat everything as normal
            return np.ones(X.shape[0])

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def score_samples(self, X):
        """
        Return anomaly scores for samples.
        The lower, the more abnormal.
        """
        if not self.is_fitted:
            return np.zeros(X.shape[0])

        X_scaled = self.scaler.transform(X)
        return self.model.score_samples(X_scaled)

    def save(self):
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted
        }, self.model_path)

    def load(self):
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            print("Model loaded from disk.")
        else:
            print("No existing model found. Initializing new model.")
            self.train([]) # Initial training with dummy data