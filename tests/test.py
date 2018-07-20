# -*- coding: utf-8 -*-
import unittest
import sys
import os

# insert the src dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import svo_extraction


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_work_flow(self):
        corpus = svo_extraction.Corpus(file_path='./sample/Murphy.txt',
                                       output_dir='./sample/out')
        corpus.set_up()
        corpus.clean_up()
        #coref = svo_extraction.Coref(corpus)
        #coref.display('neural_coref')
        nlp = svo_extraction.CoreNLP(corpus=corpus)
        nlp.exec(method='parse')

    def test_object(self):
        """

        :return:
        """
        tree_representation = open('./sample/out/tmp/parse.txt').read().split('@')[:-1]
        for each in tree_representation[-3::]:
            svo = svo_extraction.SVO(tree_representation = each)
            svo.create_tree(svo_extraction.helpers.read_tree)
            svo.tree.draw()


if __name__ == '__main__':
    test = BasicTestSuite()
    # test.test_work_flow()
    test.test_object()