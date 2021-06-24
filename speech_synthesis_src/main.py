from speech_synthesis_src.ttsMaker import TTSMaker
import json
import numpy as np
import os
from tqdm import tqdm


dataset_sentences_path = '../subset_345_sentences.json'
output_path = '../audio_dataset/'

# Importing the sentences from the JSON file
with open(dataset_sentences_path, 'r') as file:
    dataset_sentences = np.asarray(json.load(file))

assert(len(set([e[0] for e in dataset_sentences])) == len(dataset_sentences))   # Assert there is no duplicate

dataset_length = len(dataset_sentences)
print("Number of new sentences:", dataset_length)

# Initialisation of the TTS tools
ttsMaker = TTSMaker()

# Dataset generation and storing
for i, sentence in tqdm(enumerate(dataset_sentences), total=dataset_length):
    ttsMaker.IBMtts(sentence[1], os.path.join(output_path, 'IBM/', sentence[0]+'.wav'))
    ttsMaker.Microsofttts(sentence[1], os.path.join(output_path, 'Microsoft/', sentence[0]+'.wav'))
    ttsMaker.Nvidiatts(sentence[1], os.path.join(output_path, 'Nvidia/', sentence[0]+'.wav'))
    ttsMaker.basic_Gtts(sentence[1], os.path.join(output_path, 'Gtts/', sentence[0]+'.wav'))
