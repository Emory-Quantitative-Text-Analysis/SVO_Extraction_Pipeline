# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import svo_extraction
import unittest


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_absolute_truth_and_meaning(self):
        self.assertIsNone(svo_extraction.Corpus())


if __name__ == '__main__':
    corpus = svo_extraction.Corpus()
    corpus.set_up()
    corpus.clean_up()
    print(corpus)
    coref = svo_extraction.Coref(corpus)
    print(coref)
    coref.display('helpers.neural_coref')