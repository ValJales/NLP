import json
import pandas as pd

def extract_speakers():
    with open('speechs_data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    df = pd.json_normalize(data['speechs'])

    df = df[df['speakers'].apply(len) == 1]
    df['speakers'] = df['speakers'].apply(lambda x: x[0]['name'])

    df.drop(['datetime', 'readtime', 'kind'], axis=1, inplace=True)

    df.rename(columns={'speakers': 'speaker'}, inplace=True)

    return df

if __name__ == "__main__":
    df = extract_speakers()
    print(df.iloc[0])