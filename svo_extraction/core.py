import os
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
        self.file_to_use = file_path


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


    def __str__(self):
        return 'Corpus '+self.file_name+' File using '+self.file_to_use


class Coref:
    def __init__(self,corpus,coref_methods=None):

        """
        Perform different kinds of co-reference, if user want to use self-defined coref methods,
        the method need to take an input corpus object and return an output file
        :param coref_methods: list of names of co-reference methods, predefined is neural-coref
        """
        self.corpus = corpus
        if coref_methods is None:
            coref_methods = [helpers.neural_coref.__name__]
        self.coref_methods = [x for x in coref_methods]
        self.coref_files = {}

        for each in coref_methods:
            coref_file = getattr(helpers,each)(self.corpus)
            self.coref_files[each] = coref_file

        for k,v in self.coref_files.items():
            logger.info('Coref method: %s, corefed file: %s',k,v)

    def compare(self, coref_method, comparison_method=None):
        """
        Compare original file with corefed file.
        :param coref_method: String the name of the coref method
        :param comparison_method: self-defined comparison methods that take origin_text and
               corefed text as input and return two tuples of the differences that can be used
               to display the highlighting difference, the default method was implemented with difflib
        :return: tuples with highlight info
        """
        origin_text = open(self.corpus.cleaned_path).read()
        corefed_text = open(self.coref_files[coref_method]).read()
        logger.info('Comparing result from %s co-reference method',coref_method)
        if comparison_method is not None:
            logger.info('Use self-defined comparison method %s',comparison_method)
            return comparison_method(origin_text,corefed_text)

        return helpers.compare_results(origin_text,corefed_text)

    def display(self,coref_method):
        """
        Display with GUI of the difference, editing enabled
        :param coref_method: String the name of the co-reference method
        :return: the edited result
        """
        gui = helpers.GUI(title=("Comparing result from {0}".format(coref_method)))
        logger.info("Displaying result from {0}, editing enabled".format(coref_method))
        origin_display,coref_display = self.compare(coref_method)
        result = []

        # GUI to edit the corefed text
        gui.create_comparison(ta=origin_display,tb=coref_display)
        gui.create_button(text='Finish',callback=helpers.finish_comparison,
                          finish_comparison =(gui,result))
        gui.run()

        # write result to file
        f = open(self.coref_files[coref_method],'w')
        print('result is ', result[0])
        f.write(result[0])
        f.close()
        self.corpus.file_to_use = self.coref_files[coref_method]
        logger.debug('Corpus %s co-referenced, file to use now is %s',
                     self.corpus.file_name, self.corpus.file_to_use)
        return self.coref_files[coref_method]

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


class CoreNLP:
    """
    Use stanford corenlp to handle NER, co-reference and parser tree.
    """

    def __init__(self, port=None, path=None, memory=None, corpus=None):
        self.path = path if path is not None else helpers.NLP
        self.port = port if port is not None else helpers.get_open_port()
        self.memory = memory if memory is not None else '1g'
        self.corpus = corpus
        self.nlp = helpers.StanfordCoreNLP(self.path,memory=self.memory, port=self.port)

    def set_corpus(self, corpus=None):
        """
        Corpus setter wtihout reinitialize the whole nlp server
        """
        try:
            assert isinstance(Corpus,corpus)
            self.corpus = corpus
        except AssertionError:
            exit(1)

    def exec(self,method = 'word_tokenize',sentence = ''):
        """
        Exec stanfordcorenlp method name.
        :param method: choice from
                        'word_tokenize', 'pos_tag', 'ner', 'parse', 'dependency_parse', 'coref'
        :param sentence: optional kwarg to process only one sentence instead of the whole corpus
        :return: path to file holding the result
        """
        _available_method = ['word_tokenize','ner','pos_tag','parse','dependency_parse','coref']

        if method not in _available_method:
            logger.warning('This method is not available for stanfordcorenlp, available options are:{0}'.
                           format('\n'.join(_available_method)))

        if sentence == '': # process all sentences in the corpus
            logger.info('Performing {0} for {1}.'
                        .format(method,self.corpus.file_name))

            f = open(self.corpus.file_to_use, 'r')
            out_path = os.path.join(self.corpus.tmp_out,
                                    '{0}-{1}.txt'.format(self.corpus.file_name,method))
            out = open(out_path,'w')

            for line in f.readlines():
                # put delimiter into the file to separate sentences.
                print(self.nlp.__getattribute__(method)(line),'@',file=out)

            f.close()
            out.close()

            return out_path
        else:
            result = self.nlp.__getattribute__(method)(sentence)

            return result

    def exit(self):

        self.nlp.close()


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

    def __init__(self,text,
                 nlp=None,):
        """
        Take the string as input and initialize the sentence object
        :param text: str, sentence to be processed.
        """
        self.text = text

        self.nlp = nlp if nlp is not None else CoreNLP()
        self.dependency_tree = self.parse_dependency()
        self.pos_tags = self.pos_tag()
        self.tokens = self.tokenize()
        self.parse_tree = self.parse()
        self.deprel = self.set_dependency_label()

    def parse_dependency(self):
        """
        Do dependency parse of the sentence.
        :param nlp: a CoreNLP object
        :return: str representation of the dependency parse tree
        """

        logger.info("Dependency parsing \'{0}\'.".format(self.text))

        deprel =  self.nlp.exec(method='dependency_parse',sentence=self.text)

        return deprel

    def tokenize(self):
        tags = self.nlp.exec(method='pos_tag', sentence=self.text)
        # ners = self.nlp.exec(method='ner_tag',sentence=self.text)
        word_list = []
        for i in range(len(tags)):
            word = Word(tags[i][0],pos=self.pos_tags[i][1])
            lemma = helpers.lemmatize(word.text,'v' if word.pos in helpers.VERB else 'n')
            word.lemma = lemma
            word_list.append(word)
        # print(word_dic)
        return word_list

    def pos_tag(self):
        tags = self.nlp.exec(method='pos_tag',sentence=self.text)
        return tags

    def parse(self):
        tree_representation = self.nlp.exec(method='parse',sentence=self.text)
        tree = helpers.read_tree(tree_representation)
        return tree

    def set_dependency_label(self):
        """
        Set up the dependency relationship as a 2D array
        """
        matrix = [[None]*len(self.tokens) for _ in range(len(self.tokens))]
        for i in range(len(matrix)):
            matrix[i][i] = 'self'

        for label in self.dependency_tree[1:]:
            deprel = label[0]
            matrix[label[2] - 1][label[1] - 1] = deprel
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
        verb, subj, obj, adj = [], [], [], []
        svo = []
        for each in self.sentence.parse_tree.subtrees(lambda t : t.label() == 'VP'):

            tmp_subj = subj
            if each.treeposition() not in self.visited:

                self.visited.append(each.treeposition())
                obj = self._find_obj(each)
                adj = self._find_adj(each)
                subj = self._find_subj(each.parent())

                if len(subj) == 0 and each.parent().label() in ['S','SBAR']:

                    subj = tmp_subj

                verb = self._find_verbs(each,obj,adj)
                subj = subj if len(subj) != 0 else ['N/A']
                obj = obj+adj if (len(obj)!= 0 or len(adj)!=0) else ['N/A']
                for s in subj:
                    for v in verb:
                        for o in obj:
                            svo.append((s,v,o))

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
                    verb_leaves.extend(each.leaves())
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
                    subj_leaves.extend(each.leaves())
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
                obj_leaves.extend(each.leaves())
                continue
            if each.label() in ['PP','NP']:
                obj_leaves.extend(self._find_obj(each))
        return obj_leaves

    def _find_adj(self,tree):
        adj_leaves = []
        for each in tree:
            if each.label() in helpers.ADJ:
                adj_leaves.extend(each.leaves())
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


