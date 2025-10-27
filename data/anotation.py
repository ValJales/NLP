def anotate (annotation_file_path, df):
    with open(annotation_file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.split()
            df['speaker'] = df['speaker'].replace(line[0], line[1])
    return df

