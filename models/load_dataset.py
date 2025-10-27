# imports
import kagglehub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


def load_dataSet():
    """
    Description -> Download the dataSet
    params ->      None
    return ->      df : Dataframe with the dataSet
    """
    # Download latest version
    path = kagglehub.dataset_download("kapastor/democratvsrepublicantweets")

    print("Path to dataset files:", path)

    # Data Proccessing
    df = pd.read_csv(path  + "/ExtractedTweets.csv") # Load data set wi
    df.drop(['Handle'], axis=1, inplace=True) # Suppresion de la colone de Handle
    df = df[~df['Tweet'].str.contains('…', na=False)]
    df['Party'] = df['Party'].apply(lambda x: 0 if x == 'Democrat' else 1)
    return df



if __name__ == "__main__" :
    pd.set_option('display.max_colwidth', None)
    df = load_dataSet()