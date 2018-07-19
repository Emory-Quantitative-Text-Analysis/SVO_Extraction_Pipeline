import os
import sys
import spacy
import subprocess
import logging

from logging.config import fileConfig
from .core import Corpus, Coref
from .helpers import logger

SRC = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0,os.path.join(SRC,'lib','neuralcoref'))
fileConfig(os.path.join(SRC,'logging_config.ini'))

while True:
    try:
        spacy.load(os.path.join(SRC,'lib','models','en_core_web_sm','en_core_web_sm-2.0.0'))
        break
    except Exception as e:
        logger.debug('Exception %s',str(e))
        subprocess.call(['python', '-m', 'spacy', 'download', 'en'])
        # download the nlp model if not already installed