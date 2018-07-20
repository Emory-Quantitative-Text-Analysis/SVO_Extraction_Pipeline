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
        helpers.log_var('CLEANED_PATH')
        logger.debug('Corpus %s cleaned up.',self.file_name)


    def __str__(self):
        return 'Corpus '+self.file_name


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
        result = ''

        # GUI to edit the corefed text
        gui.create_comparison(ta=origin_display,tb=coref_display)
        gui.create_button(text='Finish',callback=helpers.finish_comparison,
                          finish_comparison =(gui,result))
        gui.run()

        # write result to file
        f = open(self.coref_files[coref_method],'w')
        f.write(result)
        f.close()

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


class SVO:
    """
    Subject - Verb - Object extraction objet.
    """
    def __init__(self, tree = None):
        self.tree = tree
        logger.info('Parse tree ')


class NER:
    def __init__(self,corpus = None):
        self.corpus = corpus
        logger.info(str(self.corpus),'selected for NER tagging')
