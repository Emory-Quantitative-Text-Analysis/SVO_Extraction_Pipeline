# -*- coding: utf-8 -*-
import unittest
import sys
import os

# insert the src dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import svo_extraction


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_absolute_truth_and_meaning(self):
        corpus = svo_extraction.Corpus(file_path='./sample/Murphy.txt',
                                       output_dir='./sample/out')
        corpus.set_up()
        corpus.clean_up()
        coref = svo_extraction.Coref(corpus)
        coref.display('neural_coref')


if __name__ == '__main__':
    test = BasicTestSuite().test_absolute_truth_and_meaning()