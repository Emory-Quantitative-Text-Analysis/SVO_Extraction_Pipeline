import os

from logging.config import fileConfig
from .core import helpers, Corpus, Coref, CoreNlpPipeline, SVO, Sentence
from .helpers import logger

SRC = os.path.abspath(os.path.dirname(__file__))
fileConfig(os.path.join(SRC,'logging_config.ini'))