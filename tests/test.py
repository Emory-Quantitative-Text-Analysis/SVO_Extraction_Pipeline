# -*- coding: utf-8 -*-
import unittest
import sys
import os
import ast

# insert the src dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import svo_extraction


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        corpus = svo_extraction.Corpus(file_path='./sample/Murphy.txt',
                                       output_dir='./sample/out')
        corpus.set_up()
        corpus.clean_up()
        self.corpus = corpus
        self.nlp = svo_extraction.CoreNLP(corpus=self.corpus)

    def test_work_flow(self):

        #coref = svo_extraction.Coref(corpus)
        #coref.display('neural_coref')
        nlp = svo_extraction.CoreNLP(corpus=self.corpus)
        nlp.exec(method='parse')





if __name__ == '__main__':
    text = open('./sample/Murphy.txt').read()
    # text = 'The anesthetist had warned me that the operating room would feel cold.'
    result = []
    for each in svo_extraction.helpers.split_into_sentences(text):
        nlp = svo_extraction.CoreNLP(memory='1g')
        sentence = svo_extraction.Sentence(each,nlp=nlp)
        nlp.exit()
        svo = svo_extraction.SVO(sentence)
        result.append(svo.extract())
    for each in result:
        print(each)



