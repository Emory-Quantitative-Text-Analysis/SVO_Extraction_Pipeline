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
        corpus = svo_extraction.Corpus()
        corpus.set_up()
        corpus.clean_up()
        self.corpus = corpus

    def test_work_flow(self):
        self.corpus.coref()
        self.corpus.extract_svo()





if __name__ == '__main__':
    test_case = BasicTestSuite()
    test_case.setUp()
    test_case.test_work_flow()



