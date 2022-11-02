# Written by: Adithya Tanam
# Last Update: 10/29/22

import nltk.data
import os

folder_directory_location = r"/home/adithya/Desktop/NLP_Internship/ProjectCode/PyrEvalv2/Raw/peers"
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

for file in os.listdir(folder_directory_location):
    sentence_list = []
    filepath = os.path.join(folder_directory_location, file)
    fp = open(filepath)
    data = fp.read()
    sentence_list = tokenizer.tokenize(data)
    iteration = 0
    for sentence in sentence_list:
        sent_file_name = file  + "_sentence_" + str(iteration)
        sent_file_path = os.path.join(folder_directory_location, sent_file_name)
        with open(sent_file_path, "a") as f:
            print(sentence, file=f)
        iteration += 1




