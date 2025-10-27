import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from model import load_dataSet

def train_model(df) :
    """
    Description -> Train the model
    param ->       df : dataframe
    return ->      model
    """
    # Split the data
    X = df['Tweet']
    y = df['Party']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Vectorize the data
    vectorizer = TfidfVectorizer()
    X_train = vectorizer.fit_transform(X_train)
    X_test = vectorizer.transform(X_test)

    print("X_train shape:", X_train.shape)
    print("X_test shape:", X_test.shape)
    print("caca")

if "__name__" == "__main__" :
    df = load_dataSet()
    train_model(df)
