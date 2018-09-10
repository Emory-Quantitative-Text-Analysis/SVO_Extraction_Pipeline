import os
import csv
import re
from . import helpers
logger = helpers.logger


class Corpus:
    def __init__(self,
                 file_path = None,
                 output_dir = None):
        """
        Set up variables.
        _:param: allow advanced usage to set path vars
        """
        self.file_path = file_path
        self.file_name = None
        self.output_dir = output_dir
        self.tmp_out = None
        self.cleaned_path = None
        self.corefed_path = None
        self.conll_file = None
        self.file_to_use = file_path

        self.svo_triplets = []
        self.svo_result = None

    def set_up(self):
        """
        Set up input file and output path manually
        :return:
        """
        # set up file path and file name
        while True:
            try:
                if not self.file_path:
                    helpers.show_message(msg='Select an input file', level='info')
                    self.file_path = helpers.select_file()
                    if not self.file_path: # handle cancel button
                        logger.warning('User cancel, program killed.')
                        exit(0)
                    # make sure the input file is valid
                assert os.path.exists(self.file_path) and self.file_path.endswith('.txt')
                self.file_path = os.path.abspath(self.file_path)
                break
            except AssertionError:
                helpers.show_message(msg = 'Select a valid input file',level = 'error')
        self.file_name = os.path.basename(self.file_path)[:-4]
        logger.info('Select %s for SVO extraction.', self.file_name)

        # set up output path
        while True:
            try:
                if not self.output_dir:
                    helpers.show_message(msg='Select a output folder', level='info')
                    self.output_dir = helpers.select_file(_dir= True)
                    if not self.output_dir:
                        logger.warning('User cancel, program killed.')
                        exit(0)
                    # make sure output path is valid
                assert os.path.isdir(self.output_dir)
                self.output_dir = os.path.abspath(self.output_dir)
                break
            except AssertionError:
                helpers.show_message('Please select a valid folder','error')
        # create a tmp output dir to hold intermediate files
        logger.info('Set %s as the output folder.',self.output_dir)
        self.tmp_out = os.path.join(self.output_dir, 'tmp')
        if not self.tmp_out:
            exit(0)
        os.makedirs(self.tmp_out, exist_ok=True)
        logger.debug('Create intermediate tmp output folder %s.',self.tmp_out)

        helpers.FILE_PATH = self.file_path
        helpers.FILE_NAME = self.file_name
        helpers.OUT_DIR = self.output_dir
        helpers.TMP_OUT_DIR = self.tmp_out

        logger.debug('Corpus module for %s initiated.', self.file_name)

    def clean_up(self):
        """
        Set the cleaned up path.
        """
        # first log variables
        helpers.log_var('FILE_NAME', 'FILE_PATH', 'OUT_DIR', 'TMP_OUT_DIR')
        self.cleaned_path = helpers.clean_up_file(
            file_name = self.file_name,
            file_path = self.file_path,
            tmp_out = self.tmp_out
        )
        helpers.CLEANED_PATH = self.cleaned_path
        self.file_to_use = self.cleaned_path
        helpers.log_var('CLEANED_PATH')
        logger.debug('Corpus %s cleaned up, file to use now is %s',self.file_name,self.file_to_use)

    def extract_svo(self,sentence):
        """
        Extract SVO triplets form a Sentence object.
        """
        self.svo_triplets.extend(SVO(sentence).extract())
        self.svo_result = os.path.join(self.output_dir,'SVO.csv')
        with open(self.svo_result,'w',newline='') as result:
            fieldnames = ['Sentence Index','S','V','O/A','TIME','LOCATION','PERSON','TIME_STAMP']
            svo_writer = csv.DictWriter(result,fieldnames = fieldnames)
            svo_writer.writeheader()
            for svo in self.svo_triplets:
                svo_writer.writerow({
                    'Sentence Index':svo[0],
                    'S':svo[1], 'V':svo[2], 'O/A':svo[3],
                    'TIME':svo[4],'LOCATION':svo[5] ,'PERSON':svo[6],'TIME_STAMP':svo[7],
                })


    def visualize(self):
        # TODO: Ask which kind of visualization the user want.

        return helpers.create_gexf(self),helpers.create_kml(self)

    def __str__(self):
        return 'Corpus '+self.file_name+' File using '+self.file_to_use


class Coref:

    @classmethod
    def compare(cls, origin_text, corefed_text, coref_method, comparison_method=None):
        """
        Compare original file with corefed file.
        :param coref_method: String the name of the coref method
        :param comparison_method: self-defined comparison methods that take origin_text and
               corefed text as input and return two tuples of the differences that can be used
               to display the highlighting difference, the default method was implemented with difflib
        :return: tuples with highlight info
        """
        logger.info('Comparing result from %s co-reference method',coref_method)
        if comparison_method is not None:
            logger.info('Use self-defined comparison method %s',comparison_method)
            return comparison_method(origin_text,corefed_text)

        return helpers.compare_results(origin_text,corefed_text)

    @classmethod
    def display(cls,origin_display, coref_display, coref_method):
        """
        Display with GUI of the difference, editing enabled
        :param origin_display: a tuple with difference and highlight.
        :param coref_display: a tuple with difference and highlight info
        :param coref_method: String the name of the co-reference method
        :return: the edited result
        """
        gui = helpers.GUI(title=("Comparing result from {0}".format(coref_method)))
        logger.info("Displaying result from {0}, editing enabled".format(coref_method))
        result = []

        # GUI to edit the corefed text
        gui.create_comparison(ta=origin_display,tb=coref_display)
        gui.create_button(text='Finish',callback=helpers.finish_comparison,
                          finish_comparison =(gui,result))
        gui.run()

        # write result to file
        return result[0]

    @classmethod
    def choose_coref_method(cls,coref_methods):
        """
        Choose which coref method to use
        :return: corefed file path
        """
        gui = helpers.GUI(title = "Choosing coref method to use.")
        helpers.show_message(msg="Please choose a coref method you wish to use.")
        logger.info("Choosing coref method")
        method = None
        gui.create_options(options = coref_methods)
        gui.create_button(text='Choose',callback=helpers.finish_options,
                          finish_options = (gui,method))
        return method

    def __str__(self):
        return '/n'.join([str(x) for x in self.coref_files])


class Actor:
    """
    Actor list to filter the SVO triplet
    """

    def __init__(self):
        self.actor_filter = None
        self.actor_list = None

    def get_filter(self, criteria=None):
        """
        Get social actors of the corpus.
        :param criteria: a list of  actors, default is to extract from WordNet
        :return: a list of social actors from the corpus
        """
        if criteria is None:
            self.actor_filter = helpers.wordnet_social_actor()
            result = ''
            # GUI to edit social actors filter
            helpers.show_message('Please edit social actor list that you wish to use.')
            gui = helpers.GUI(title='Editing social actor list from WordNet')
            gui.create_list(text=self.actor_filter, label='Social Actor List')
            gui.create_button(text='Finish',
                              command=helpers.finish_edit,
                              finish_edit=(gui, result))

        else:
            self.actor_filter = criteria

    def get_actor(self):
        return


class CoreNlpPipeline:
    """
    Use stanford corenlp to handle NER, co-reference and parser tree.
    """

    def __init__(self, corpus=None):

        self.corpus = corpus

    def setUp(self):

        conll_file, self.corefed_files = helpers.stanford_pipeline(self.corpus)
        self.corpus.conll_file = conll_file

    def setup_coref(self):
        origin_text = open(self.corpus.file_to_use).read()
        coref_methods = []
        for each in self.corefed_files:
            corefed_text = open(each).read()
            coref_method = os.path.basename(each).split('-')[-2]
            coref_methods.append(coref_method)
            origin_dispaly, coref_display = \
                Coref.compare(origin_text,corefed_text,coref_method)
            edited_coref = \
                Coref.display(origin_dispaly,coref_display,coref_method)
            open(each,'w').write(edited_coref)

        method_chosen = Coref.choose_coref_method(coref_methods)

        self.corpus.file_to_use = os.path.join(self.corpus.tmp_out,
                                               '-'+method_chosen+'corefed-cleanup.txt')

    def interepret_annotation(self):
        conll = open(os.path.join(self.corpus.tmp_out,self.corpus.file_name+'-conll.txt')).read()
        d = "@@@Sentence"
        # print(conll,conll.split("@@@Sentence")[1::])
        for block in [d+e for e in conll.split("@@@Sentence")[1::]]:
            # print(block.split("@@@"))
            sentence = Sentence(block.split("@@@"))
            self.corpus.extract_svo(sentence)



class Word:
    """
    Word object with semantic information and deprel
    """

    def __init__(self,text,pos=None,ner=None):
        self.text=text
        self.pos=pos
        self.ner=ner
        self.lemma = text


class Sentence:
    """
    Sentence object with semantic information tagged.
    """

    def __init__(self,conll_block):
        """
        Take the annotation as input and initialize the sentence object
        :param text: str, sentence to be processed.
        """
        self.conll_block = conll_block
        self.index = self.get_index()
        self.text = self.get_text()
        self.token_list,self.time_list, self.location_list, self.person_list,self.time_stamp\
            = self.tokenize()
        self.parse_tree = self.get_parser()
        self.dependency = self.set_dependency_label()

    def get_index(self):
        """
        Find the index of this sentence in the corpus.
        """
        assert self.conll_block[1].split("\n")[0].startswith("Sentence")
        index = re.findall(r'\d+',self.conll_block[1].split("\n")[0])[0]
        return index

    def get_text(self):
        """
        Restore the original sentence.
        """
        assert self.conll_block[1].split("\n")[0].startswith("Sentence")
        sentence = self.conll_block[1].split("\n")[1]
        return sentence

    def tokenize(self):
        """
        Generate Word object with semantic info tagged.
        """
        token_list = []
        time_list = []
        location_list = []
        person_list = []
        time_stamp =(helpers.EPOCH+
                     helpers.datetime.timedelta(days=int(self.index)))\
                     .strftime("%Y-%m-%d")
        assert self.conll_block[2].split("\n")[0] == "token"
        tokens = self.conll_block[2].split("\n")[1:-1]
        for each in tokens:
            tag_list = each.split("\t")
            word = Word(tag_list[0],
                        pos = tag_list[1],
                        ner = tag_list[2])
            token_list.append(word)
            if tag_list[2] in ['DURATION','DATE','TIME']:
                time_list.append(tag_list[0])
            elif tag_list[2] == 'LOCATION':
                location_list.append(tag_list[0])
            elif tag_list[2] == 'PERSON':
                person_list.append(tag_list[0])
        return token_list, time_list,\
               " ".join(location_list), \
               " ".join(person_list),\
               time_stamp

    def get_parser(self):
        """
        Restore parser tree.
        """
        assert self.conll_block[3].split("\n")[0] == "parse"
        tree_representation = self.conll_block[3].split("\n")[1]
        tree = helpers.read_tree(tree_representation)
        return tree

    def set_dependency_label(self):
        """
        Set up the dependency relationship for subtrees in parser_tree.
        """
        assert self.conll_block[4].split("\n")[0] == "dependency"
        matrix = [[None]*len(self.token_list) for _ in range(len(self.token_list))]
        for i in range(len(matrix)):
            matrix[i][i] = 'self'
        for each in self.conll_block[4].split("\n")[1:-1]:
            deprel = each[:each.find('(')]
            print(each[each.find('-')+1:each.find(',')],
                  each[each.rfind('-')+1:each.find('_')]
                  )
            i = int(each[each.find('-')+1:each.find(',')])
            j = int(each[each.rfind('-')+1:each.find('_')])
            if i-1 in range(0,len(self.token_list)) and j-1 in range(0,len(self.token_list)):
                matrix[i-1][j-1] = deprel

        index = 0
        for t in self.parse_tree.subtrees(lambda e : e.height() == 2):
            t.set_deprel(matrix[index])
            index += 1
        return matrix

class SVO:
    """
    Subject - Verb - Object extraction object for each sentence.
    """
    def __init__(self, sentence):
        """
        Initialize SVO with a string representation of tree or a tree object.
        :param sentence: Sentence object
        :param nlp: a CoreNLP object
        """

        self.sentence = sentence
        self.visited = []
        # Decrypted attributes
        # self.tree_representation = tree_representation
        # self.tree_interpreter = tree_interpreter
        # self.tree = tree

    def extract(self):
        """
        Extract SVO/SVA triplet (not filtered by it's deprel), the algorithm is recursive
        and should be intuitive, so I will not explain it here.
        :return:
        """
        verb, subj,tmp_subj, obj, adj = [], [], [], [],[]
        sentence_index, time,location, persons,time_stamp = \
            self.sentence.index, self.sentence.time_list, self.sentence.location_list, self.sentence.person_list,self.sentence.time_stamp
        svo = []
        for each in self.sentence.parse_tree.subtrees(lambda t : t.label() == 'VP'):

            if each.treeposition() not in self.visited:

                self.visited.append(each.treeposition())
                obj = self._find_obj(each)
                adj = self._find_adj(each)
                subj = self._find_subj(each.parent())

                if len(subj) == 0 and each.parent().label() in ['S','SBAR']:

                    subj = tmp_subj

                verb = self._find_verbs(each,obj,adj)

                tmp_subj = subj
                for s in subj:
                    for v in verb:
                        if s and v and s.get_deprel(v) == 'nsubjpass':
                            _tmp = subj[::]
                            subj = obj[::]
                            obj = _tmp[::]
                            break
                    else:
                        continue
                    break

                v_i = 0  # verb index to mute
                for v_1 in verb:
                    for v_2 in verb:
                        if v_2:
                            print(v_1.get_str(), v_2.get_str(), v_1.get_deprel(v_2))
                            if v_1.get_deprel(v_2) in ['aux', 'auxpass']:
                                verb[v_i] = None
                    v_i += 1

                subj = [e.get_str() for e in subj]
                obj = [e.get_str() for e in obj+adj]
                verb = [e.get_str() for e in verb if e]

                for s in subj:
                    for v in verb:
                        for o in obj:
                            svo.append((sentence_index,
                                        s,v,o,
                                        time,location,persons,time_stamp))

                if len(verb) != 0:
                    print(subj,verb,obj,adj,flush=True)
                else:
                    print('No valid ',flush=True)
        return svo

    def _find_verbs(self,tree,obj,adj):
        verb_leaves = []
        for each in tree:
            if isinstance(each,helpers.ParentedTree):
                if each.label() in helpers.VERB:
                    verb_leaves.extend(list(each.subtrees(lambda t: t.height() == 2)))
                    continue

                if each.label() == 'VP':
                    # has child as Verb, parent carries all child's verb leaves
                    if each.treeposition() not in self.visited:
                        self.visited.append(each.treeposition())
                        obj += self._find_obj(each)
                        adj += self._find_adj(each)
                        verb_leaves.extend(self._find_verbs(each,obj,adj))


        return verb_leaves

    def _find_subj(self,tree):
        # find the left siblings labeled with NP, which can be later filtered or altered by deprel
        subj_leaves = []
        for each in tree:
            if isinstance(each,helpers.ParentedTree):
                if each.label() in helpers.NOUN:
                    subj_leaves.extend(list(each.subtrees(lambda t: t.height() == 2)))
                    continue

                if each.label() in ['PP','NP']:
                    subj_leaves.extend(self._find_subj(each))

                if each.label() == 'VP':
                    break

        return subj_leaves

    def _find_obj(self,tree):
        obj_leaves = []
        for each in tree:
            if each.label() in helpers.NOUN:
                obj_leaves.extend(list(each.subtrees(lambda t: t.height() == 2)))
                continue
            if each.label() in ['PP','NP']:
                obj_leaves.extend(self._find_obj(each))
        return obj_leaves

    def _find_adj(self,tree):
        adj_leaves = []
        for each in tree:
            if each.label() in helpers.ADJ:
                adj_leaves.extend(list(each.subtrees(lambda t: t.height() == 2)))
                continue
            if each.label() == 'ADJP':
                adj_leaves.extend(self._find_adj(each))
        return adj_leaves

    # ==================== Decrypted methods ==============================
    """
    def extract(self):
        index = 0
        svo_list = []
        for each in self.sentence.tokens:
            if each.pos in helpers.VERB:
                # iterate through all verbs that are not auxiliary verbs
                verb = each
                subj = self._find_subject_for_verb(verb)
                obj = self._find_object_for_verb(verb)

                # TODO: copula case

            index += 1
        return svo_list

    def _find_subject_for_verb(self,verb):
        _subj = []
        
        index = self.sentence.word_dic[verb.text]
        i = 0
        assert verb.pos in helpers.VERB # make sure we are dealing with verbs
        for each in self.sentence.deprel:
            if each[index] == 'nsubj':
                _subj.append(self.sentence.tokens[i])
            i += 1
        return _subj

    def _find_object_for_verb(self,verb):
        _obj = []
        index = self.sentence.word_dic[verb.text]
        i = 0
        for each in self.sentence.deprel:
            if each[index] == 'dobj':
                print(each)
                _obj.append(self.sentence.tokens[i])
            i += 1

        return _obj

    @classmethod
    def _check_nmod(cls,deprel):
        if 'nmod' in deprel:
            return deprel.index('nmod')
        return -1

    @classmethod
    def _check_rcl(cls,deprel):
        if 'acl:relcl' in deprel:
            return deprel.index('acl:relcl')
        return -1
    """