import pandas as pd
import json

def anotate (annotation_file_path, df):
    with open(annotation_file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.split(',')
            speaker = line[0]
            political_range = line[1].strip('\n')
            df['speaker'] = df['speaker'].replace(speaker, political_range)
    return df

def clean_data(df):
    # Remove rows with speaker column as not integer
    df = df[df['speaker'].apply(lambda x: x.isdigit())]
    # Convert the speaker column to integer
    df['speaker'] = df['speaker'].astype(int)

    # Remove rows with text are NoneType
    df = df[df['text'].notnull()]
    #remove NaN
    df = df.dropna(subset=['text'])

    df['text'] = df['text'].astype(str)

    # Remove rows with text column as empty
    df = df[df['text'].str.strip() != '']  

    return df

def load_speech_file(filepath):
    # Assuming you have the JSON file named 'speeches.json'
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extracting the speeches data
    speeches = data.get('speechs', [])

    # Create a list of dictionaries to store the relevant data
    speech_data = []
    for speech in speeches:
        # Extracting necessary details from each speech
        title = speech.get('title', '')
        speakers = [speaker['name'] for speaker in speech.get('speakers', [])]
        if (len(speakers) != 1):
            continue

        # Extracting other details


        context = speech.get('context', '')
        keywords = ', '.join(speech.get('keywords', []))
        thematics = ', '.join(speech.get('thematics', []))
        datetime = speech.get('datetime', '')
        readtime = speech.get('readtime', '')
        kind = speech.get('kind', '')
        text = speech.get('text', '')


        #check if text is None
        if (text is None):
            #print("text is None")
            continue
        # Check if there is exactly one speaker
        if (len(speakers) != 1):
            continue

        speech_data.append({
            #'title': title,
            'speaker': speakers[0],
            #'context': context,
            #'keywords': keywords,
            #'thematics': thematics,
            #'datetime': datetime,
            #'readtime': readtime,
            #'kind': kind,
            'text': text
        })

    # Creating a DataFrame from the extracted data
    df = pd.DataFrame(speech_data)

    return df

def load_speech_data(filepath, anntotation_path):
    df = load_speech_file(filepath)
    df = anotate(anntotation_path, df)
    df = clean_data(df)
    return df

if __name__ == "__main__":
    # Example usage
    filepath = 'data/speechs_data.json'
    annotation_path = 'data/annotated_speakers.csv'
    df = load_speech_data(filepath, annotation_path)
    print(df.head())