from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig

import torch
import numpy as np
from scipy.io.wavfile import write

from gtts import gTTS

import os
import errno


class TTSMaker:
    """
    Class implementing/giving access to 4 Text-To-Speech methods:
    - GTTS (python library)
    - Nvidia Tachotron2 & Waveglow (pre-trained Deep Neural Network loaded through pytorch)
    - IBM Watson: Cloud service, you'll need to add in the code your api key (see class atributes)
    - Microsoft Azure: Cloud service, you'll need to add in the code your api key (see class atributes)
    """

    # Follow the instructions on IBM Watson's website to generate your key and url
    ibm_key = 'my_key'
    ibm_service_url = 'my_url_instance'

    # Follow the instructions on Microsoft Azure's website to generate your api key
    microsoft_key = "my_key"
    microsoft_region = "westeurope"     # Change if necessary

    def __init__(self):
        """Init function of the TTSMaker class, initialize the communication with IBM Watson and Microsoft Azure
        services, and loads Nvidia's Tachotron and Waveglow pre-trained models"""
        self.ibm_authenticator = IAMAuthenticator(self.ibm_key)
        self.ibm_tts_object = TextToSpeechV1(authenticator=self.ibm_authenticator)
        self.ibm_tts_object.set_service_url(self.ibm_service_url)

        self.microsoft_speech_config = SpeechConfig(subscription=self.microsoft_key,
                                                    region=self.microsoft_region)

        # Loading Nvidia's model and checkpoint from pytorch
        self.device = 'cpu'
        self.waveglow = torch.hub.load('nvidia/DeepLearningExamples:torchhub', 'nvidia_waveglow')
        self.waveglow = self.waveglow.remove_weightnorm(self.waveglow)
        self.waveglow = self.waveglow.to(self.device)
        self.waveglow.eval()
        self.tacotron2 = torch.hub.load('nvidia/DeepLearningExamples:torchhub', 'nvidia_tacotron2')
        self.tacotron2 = self.tacotron2.to(self.device)
        self.tacotron2.eval()

    def IBMtts(self, text, path):
        """
        Generates an audio file containing the synthetize spoken version of the text input with IBM Watson services
            :param text: The sentence to synthetize (string)
            :param path: The relative/absolute path where to save the generated audio (string)
        """

        if not os.path.exists(os.path.dirname(path)):
            self.create_dir(path)

        with open(path, 'wb') as audio_file:
            res = self.ibm_tts_object.synthesize(
                text,
                voice='en-US_AllisonV3Voice',
                accept='audio/wav').get_result()
            audio_file.write(res.content)

    def Microsofttts(self, text, path):
        """
        Generates an audio file containing the synthetize spoken version of the text input with Microsoft Azure services
            :param text: The sentence to synthetize (string)
            :param path: The relative/absolute path where to save the generated audio (string)
        """

        if not os.path.exists(os.path.dirname(path)):
            self.create_dir(path)
        if not os.path.exists(path):    # TODO: not working...
            audio_config = AudioOutputConfig(filename=path)
            synthesizer = SpeechSynthesizer(speech_config=self.microsoft_speech_config, audio_config=audio_config)
            synthesizer.speak_text_async(text)

    def Nvidiatts(self, text, path):
        """
        Generates an audio file containing the synthetize spoken version of the text input with Nvidia's Tachotron and
        Waveglow pre-trained models.
            :param text: The sentence to synthetize (string)
            :param path: The relative/absolute path where to save the generated audio (string)
        """

        if not os.path.exists(os.path.dirname(path)):
            self.create_dir(path)

        sequence = np.array(self.tacotron2.text_to_sequence(text, ['english_cleaners']))[None, :]
        sequence = torch.from_numpy(sequence).to(device=self.device, dtype=torch.int64)

        # run the models
        with torch.no_grad():
            _, mel, _, _ = self.tacotron2.infer(sequence)
            audio = self.waveglow.infer(mel)
        audio_numpy = audio[0].data.cpu().numpy()
        rate = 22050

        write(path, rate, audio_numpy)

    def basic_Gtts(self, text, path):
        """
        Generates an audio file containing the synthetize spoken version of the text input with the Gtts library
            :param text: The sentence to synthetize (string)
            :param path: The relative/absolute path where to save the generated audio (string)
        """

        if not os.path.exists(os.path.dirname(path)):
            self.create_dir(path)

        audio = gTTS(text)
        audio.save(path)

    @staticmethod
    def create_dir(path):
        """Creates the last directory contained in the parameter path.
        The previous directories of the path are expected to exist."""
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
