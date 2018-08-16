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
        self.corpus = svo_extraction.Corpus()
        self.corpus.set_up()
        self.corpus.clean_up()
        print(self.corpus)

    def testCoreNlpPipeline(self):
        nlp = svo_extraction.CoreNlpPipeline(corpus=self.corpus)
        nlp.setUp()
        nlp.interepret_annotation()
        print(self.corpus.svo_triplets)





if __name__ == '__main__':
    test_case = BasicTestSuite()
    test_case.setUp()
    test_case.testCoreNlpPipeline()



