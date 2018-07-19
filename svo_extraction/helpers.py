# coding: utf-8

# helper methods and models for svopipeline

import glob
import os
import sys
import subprocess
import time
import re
import string
import logging
import difflib as df
import tkinter as tk

from tkinter import Tk,messagebox
from tkinter.filedialog import askopenfilename,askdirectory

from nltk.stem.wordnet import WordNetLemmatizer
from nltk import StanfordNERTagger
from .lib.neuralcoref import neuralcoref as nc

# ========================= Variables and  Models ======================== #
# ========== dir variables ========== #
SRC = os.path.dirname(__file__) # scripts
LIB = os.path.join(SRC,'lib')

# ========= set up logger  ========== #
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.debug('Sth')


def my_handler(type, value, tb):
    """
    Automatically log all uncaught exception to file
    """
    logger.exception("Uncaught exception: {0}, of type {1}, {2}".format(str(value),type,tb))


# Install exception handler
sys.excepthook = my_handler


def log_var(*args,local=False):
    """
    Method to simply format logging variables
    :param args: list of args to log
    :return:
    """
    if not local:
        for k in args:
            if k in globals() and globals()[k] is not None:
                if os.path.exists(globals()[k]):
                    logger.debug("Variable %s set as: %s",k,
                                 os.path.normpath(os.path.abspath(globals()[k])))
                else:
                    logger.debug("Variable %s set as: %s", k,globals()[k])
            else:
                logger.debug("Variables %s is not set yet",k)
    else:
        for k in args:
            if k in locals() and locals()[k] is not None:
                if os.path.exists(locals()[k]):
                    logger.debug("Variable %s set as: %s",k,
                                 os.path.normpath(os.path.abspath(locals()[k])))
                else:
                    logger.debug("Variable %s set as: %s", k,locals()[k])
            else:
                logger.debug("Variables %s is not set yet",k)


def exception(_logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    def _decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                # log the exception
                err = "There was an exception in  "
                err += func.__name__
                _logger.exception(err)

                # re-raise the exception
                raise

        return wrapper
    return _decorator

# ========== set up NLP models ======== #
NER_MODEL = os.path.join(LIB,'./edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz')
NER_JAR = os.path.join(LIB,'./edu/stanford/stanford-ner.jar')
ner_tagger = StanfordNERTagger(NER_MODEL,NER_JAR)

# ======== data variables =========== #
FILE_NAME = None
FILE_PATH = None
OUT_DIR = None
TMP_OUT_DIR = None

# ======== flags variables ========== #
NER_TAGGED = False
CLEANED = False
COREFED = False
ACTOR_FILTERED = False

DO_GEPHI = False
DO_MAP = False
DO_NGRAM = False
# ============================ GUI Utility Method =============================== #


def finish_comparison(gui,result=None):
    if result is None:
        result=[]
    edited = gui.b.get('1.0',tk.END)
    result.append(edited)
    gui.root.destroy()


def finish_selection(gui,selection,candidate,result=None):
    if result is None:
        result = []
    for each in selection.curselection():
        result.append(candidate[each])
    gui.root.destroy()


def finish_select_all(gui,candidate,result=None):
    if result is None:
        result = []
    result[:] = candidate[::] # use all social actors contained
    gui.root.destroy()


def finish_select_none(gui,result=None):
    if result is None:
        result = []
    result[:] = []
    gui.root.destroy()


class GUI:
    """
    GUI module to assist user interface design.
    """

    class List:
        def __init__(self,gui,text=None, label=''):
            """
            Create text for display
            :param text: list of str to display
            :param label: list label
            """
            if text is None:
                text = []
            self.list_label = tk.Label(gui.root, text=label)
            self.list = tk.Text(gui.list_frame, width=20)
            self.list.insert(tk.INSERT, '\n'.join(text))

    class Comparison:
        def __init__(self,gui,ta=None,tb=None):

            self.a = tk.Text(gui.comparison_frame)

            for i in range(len(ta)):
                each = ta[i]
                self.a.insert(tk.INSERT, each[0] + '\n')

                for highlight in each[1]:
                    self.a.tag_add("here",
                                   str(i + 1) + "." + str(highlight[0]),
                                   str(i + 1) + "." + str(highlight[1]))
                    self.a.tag_config("here",
                                      background="yellow", foreground="blue")

            self.b = tk.Text(gui.comparison_frame)

            for i in range(len(tb)):
                each = tb[i]
                self.b.insert(tk.INSERT, each[0] + '\n')

                for highlight in each[1]:
                    self.b.tag_add("here",
                                   str(i + 1) + "." + str(highlight[0]),
                                   str(i + 1) + "." + str(highlight[1]))
                    self.b.tag_config("here",
                                      background="red", foreground="blue")

    class Selection:
        def __init__(self,gui,text=None):
            if text is None:
                text = []
            self.selection = tk.Listbox(gui.selection_frame,
                                        selectmode=tk.MULTIPLE)
            for i in range(len(text)):
                self.selection.insert(i+1,text[i])

    def __init__(self,title=''):
        self.root = tk.Tk()
        self.root.title(title)
        self.button = None

        # list frame
        self.list_frame = None

        # comparison frame
        self.comparison_frame = None

        # selection frame
        self.selection_frame = None

    def create_list(self,text=None, label=''):
        """
        Create text for display
        :param text: list of str to display
        :param label: list label
        """
        _list = self.List(self,text=text, label=label)
        if self.list_frame is None:
            self.list_frame = tk.Frame(self.root)
        _list.list_label.pack(padx=30, pady=10, side=tk.LEFT)
        _list.list.pack(padx=5, pady=10, side=tk.LEFT)

    def create_comparison(self, ta=None, tb=None):
        """
        Create text for comparison.
        :param ta: Original text with highlight info of diff
        :param tb: Text to compared to with highlight info of diff
        """
        _comparison = self.Comparison(self,ta=ta,tb=tb)
        if self.comparison_frame is None:
            self.comparison_frame = tk.Frame(self.root)
        _comparison.a.pack(padx=5, pady=10, side=tk.LEFT)
        _comparison.b.pack(padx=5, pady=20, side=tk.LEFT)

    def create_selection(self,text=None):
        """
        Create selection of list of text
        :param text: list of text to be selected from
        """
        _selection = self.Selection(self,text=text)
        if self.selection_frame is None:
            self.selection_frame = tk.Frame(self.root)
        _selection.selection.pack(padx=5,pady=10,side=tk.LEFT)

    def create_button(self,*args,text='',callback=None,**kwargs ):
        """
        Create button
        :param text: text of the button
        :param callback: callback function
        :param args: args for callback function
        :param kwargs: kwargs for callback function
        :return:
        """
        self.button = tk.Button(self.root,
                                text=text,
                                command=lambda: callback(self,*args,**kwargs))
        self.button.pack()

# ======== select input file ========= #


def select_file(_dir=False):
    """
    Ask user to select a file
    :param _dir : can be a dir or not
    :return: input file path or a dir
    """
    Tk().withdraw()
    if not _dir:
        return askopenfilename()
    else:
        return askdirectory()

# ============= message box ============== #


def show_message(msg = '', level = 'info'):
    """
    Pop up a message box
    :param msg: message to show
    :param level: info or warning or error
    :return:
    """
    Tk().withdraw()
    if level == 'info':
        messagebox.showinfo("Info",msg)
    elif level == 'warning':
        messagebox.showwarning("Warning",msg)
    elif level == 'error':
        messagebox.showerror("Error",msg)
# ========================== Utility Methods ============================= #

# ======== split into sentences ============ #
# https://stackoverflow.com/questions/4576077/python-split-text-on-sentences
caps = "([A-HJ-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"


def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

# ======= corpus clean-up ======= #


def clean_up_file(file_name = None, file_path = None, tmp_out = None):
    """

    :param file_name: file name that is going to be cleaned up
    :param file_path: file path to the file being cleaned up
    :param tmp_out: tmp output dir to hold the cleaned up result
    :return: path to the cleaned up file
    """
    logger.debug('Cleaning up %s',file_name)
    clean_path = os.path.join(tmp_out, file_name+'-cleanup.txt')
    file = open(file_path)
    with open(clean_path, 'w') as out:
        lines = split_into_sentences(file.read())
        for line in lines:
            line = line.replace('Q:','').replace('A:','')
            line = line.replace(u"â $ ™", "'").replace(u"â€™","'")
            line = line.replace(u'â $', '').replace(u'œ', '').replace("''", '').replace("``", '')
            line = line.replace(u"¦", '').replace(u"™", '').strip()
            # print(line)
            line = ''.join(filter(lambda x: x in string.printable or x == '\'',line))
            # print(line)
            if is_sentence(line):
                out.write(line)
                out.write('\n') # separate to lines
    return clean_path


def is_sentence(sentence):
    """
    Check if a line is sentence.
    """
    if len(sentence.split()) < 5:
        return False
    if sentence[-1] not in string.punctuation:
        return False
    if sentence.isupper():
        return False
    if sentence.istitle():
        return False
    count = 0
    for token in sentence.split():
        if len(token) >=2 and token.isupper():
            count += 1
        if token.strip('.').isnumeric():
            count += 1
        elif token in ['p.', 'Vol.', 'pp.', 'Published']:
            count +=3
        if count >=3:
            return False
    return True


def is_title(sentence):
    """
    Check if a line is title.
    """
    title_length_limit = 5
    if sentence[-1] not in string.punctuation:
        if len(sentence) < title_length_limit:
            # print sentence
            return True
    if sentence.isupper():
        # print sentence
        return True
    if sentence.istitle():
        # print sentence
        return True

def ner_tag_sentence(sentence):
    # need to set JAVAHOME in syspath
    while 'JAVAHOME' not in os.environ:
        show_message(
            'NER Tagger require the JAVAHOME path to be set, please specify your java.exe file path. Typically it\'s \
            some where like C:/Program Files/Java/jdk1.8.0_161/bin/java.exe, please use backslash in path:\n',
            level = 'info'
            )
        java_path = select_file()
        os.environ['JAVAHOME'] = java_path

    while True:
        try:
            return ner_tagger.tag(sentence.split())
        except (LookupError, OSError) as e:
            logger.exception(str(e)+' occured')
            java_path = input(
            'Your JAVAHOME path is not correct, please try specify the path again:\n'
            )
        os.environ['JAVAHOME'] = java_path


#=========================Coref Utility Method========================#
def neural_coref(corpus):
    """
    This method uses the neuralCoref library to perform coreference,
    generally speaking, this usually gave better result than the CoreNLP approach
    TODO: Optimize the model loading process, right now it's trivial
    """
    logger.info('Neural Coreferencing...')
    coref = nc.Coref()
    out_path = os.path.join(corpus.tmp_out,corpus.file_name+'-neuralcorefed.txt')
    sentences = split_into_sentences(open(corpus.cleaned_path,'r',
                                          encoding='utf-8',errors="ignore").read())
    coref.continuous_coref(utterances = sentences)
    out = open(out_path,'w')
    out.write('\n'.join(coref.get_resolved_utterances()))
    out.close()
    cleaned_neural_coref = clean_up_file(file_name = corpus.file_name+'-neuralcorefed',
                                         file_path = out_path,
                                         tmp_out = corpus.tmp_out
                                         )
    log_var('out','cleaned_neural_coref')
    return cleaned_neural_coref


def coref(corpus, System = 'statistical'):
    """
    This method call an external .jar routine to perform CoreNLP coreference
    # TODO: The difference between corefed and origin is not accurate. Please fix it.
    # 		Maybe consider fetch that information from the coref.java routine.
    """
    logger.info('Coreferencing...')
    tmp = os.getcwd()
    os.chdir(LIB)
    logger.warning('Switching to %s folder.', LIB)
    # subprocess to execute stanford coref routine with 256mb    memory space
    subprocess.call(['java', '-Xmx1024m','Coref',
                    '-inputFile', corpus.cleaned_path,
                    '-outputDir', corpus.tmp_out,
                    '-system',System])
    os.chdir(tmp)
    logger.warning('Switching to %s folder.',tmp)
    out_path = os.path.join(corpus.tmp_out,corpus.file_name+"-"+System+"-out.txt")
    cleaned_coref = clean_up_file(file_name = corpus.file_name+"-"+System+'corefed',
                                     file_path = out_path,
                                     tmp_out = corpus.tmp_out)
    log_var('out','cleaned_coref')
    return cleaned_coref


def compare_results(origin_text,corefed_text):
    origin_sentences = split_into_sentences(origin_text)
    corefed_sentences = split_into_sentences(corefed_text)
    origin_display = []
    corefed_display = []
    """
    SequenceMatcher gave matching point for each sentences;
    We use this to find the difference.
    """
    for i in range(0, min(len(corefed_sentences), len(origin_sentences))):

        origin_display_highlighted = []
        corefed_display_highlighted = []

        origin_len = 0
        corefed_len = 0

        # mark junk characters " ' tab and space
        s = df.SequenceMatcher(lambda x: x in " \'\t\"",
                               origin_sentences[i], corefed_sentences[i], autojunk=False)
        matching = s.get_matching_blocks()

        for j in range(0, len(matching) - 1):
            start = matching[j]
            end = matching[j + 1]

            origin_display_highlighted.append((start[0] + start[2] + origin_len,
                                               end[0] + origin_len))
            corefed_display_highlighted.append((start[1] + start[2] + corefed_len,
                                                end[1] + corefed_len))

        origin_len += end[0]
        corefed_len += end[1]

        origin_display_tuple = (origin_sentences[i],
                                origin_display_highlighted)

        corefed_display_tuple = (corefed_sentences[i],
                                 corefed_display_highlighted)

        origin_display.append(origin_display_tuple)
        corefed_display.append(corefed_display_tuple)

