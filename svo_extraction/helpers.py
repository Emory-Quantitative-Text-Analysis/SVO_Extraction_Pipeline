# coding: utf-8

# helper methods and models for svopipeline

import glob
import os
import sys
import csv
import hashlib
import subprocess
import datetime
import inspect
import traceback
import re
import string
import random
import logging
import socket
import difflib as df
import tkinter as tk

from contextlib import closing
from tkinter import Tk,messagebox,Entry, Label, Button
from tkinter.filedialog import askopenfilename,askdirectory

from nltk.tree import *
import nltk.draw
from nltk.stem import WordNetLemmatizer

import simplekml
from geopy.geocoders import Nominatim

from .lib.gexf._gexf import Gexf, Spells, Node, Edge
# ========================= Variables and  Models ======================== #

# ========== dir variables ========== #
SRC = os.path.dirname(__file__) # scripts
LIB = os.path.join(SRC,'lib')
NLP = os.path.abspath(os.path.join(LIB,
                                   'edu',
                                   'stanford',
                                   'stanford-corenlp-full-2018-02-27'))
# ========= SVO Rules ==============#
NOUN = ["NN", "NNP", "NNPS","NNS","PRP"]
VERB = ["VB","VBD","VBG","VBN", "VBP", "VBZ"]
ADJ = ["JJ","JJR","JJS"]
REL_PRP = ["who","whom","that","which"]

SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
OBJECTS = ["dobj", "dative", "attr", "oprd"]

# TODO: Handle passive tense, we will need dependency parser for this one, but the tree \
# TODO:       representation can't handle this yet.
# ========= set up logger  ========== #
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def my_handler(type, value, tb):
    """
    Automatically log all uncaught exception to file
    """
    logger.exception("Uncaught exception: {0}, of type {1}\n Traceback:{2}"
                     .format(str(value),type,'\n'.join(traceback.format_tb(tb=tb))))


# Install exception handler
sys.excepthook = my_handler


def log_var(*args):
    """
    Method to simply format logging variables
    :param args: list of args to log, var for local variable, name for global variables
    """
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    local_vars = {}

    for var_name, var_val in callers_local_vars:

        if var_val in args:
            local_vars[var_name] = var_val

    for k,v in local_vars.items():
        logger.debug("Variable %s set as: %s", k, v)

    for k in args:

        if k not in globals():
            continue

        elif k in globals() and globals()[k] is not None:

            if os.path.exists(globals()[k]):
                logger.debug("Variable %s set as: %s",k,
                             os.path.normpath(os.path.abspath(globals()[k])))
            else:
                logger.debug("Variable %s set as: %s", k,globals()[k])

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
wnl = WordNetLemmatizer()

# ========== set up Geolocator ======== #
geolocator = Nominatim()

# ======== data variables =========== #
FILE_NAME = None
FILE_PATH = None
OUT_DIR = None
TMP_OUT_DIR = None

EPOCH = datetime.datetime.today()

# ======== flags variables ========== #
NER_TAGGED = False
CLEANED = False
COREFED = False
ACTOR_FILTERED = False

DO_GEPHI = False
DO_MAP = False
DO_NGRAM = False
DEFAULT_LOCATION = None

# ===================== Port Checking Utility Method ======================= #


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            print ("Port is open")
        else:
            print ("Port is not open")


def get_open_port():
    # function to find a open port on local host
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

# ============================ GUI Utility Method =============================== #


def finish_comparison(gui,result):
    edited = gui._comparison.b.get('1.0',tk.END)
    result.append(edited)
    gui.root.destroy()


def finish_edit(gui,result):
    edited = gui._list('1.0',tk.END)
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


def finish_options(gui,method=''):
    # TODO: fix access protected attribute

    method = gui._options.variable.get()
    gui.root.destry()



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

    class Option:
        def __init__(self,gui,options=None):
            if options is None:
                options = []
            self.variable = tk.StringVar(gui.root)
            self.variable.set(options[0])
            self.options = tk.OptionMenu(gui.root,self.variable,options)

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

        # options frame
        self.options_frame = None

    def create_list(self,text=None, label=''):
        """
        Create text for display
        :param text: list of str to display
        :param label: list label
        """
        self._list = self.List(self,text=text, label=label)
        if self.list_frame is None:
            self.list_frame = tk.Frame(self.root)
        self._list.list_label.pack(padx=30, pady=10, side=tk.LEFT)
        self._list.list.pack(padx=5, pady=10, side=tk.LEFT)

    def create_comparison(self, ta=None, tb=None):
        """
        Create text for comparison.
        :param ta: Original text with highlight info of diff
        :param tb: Text to compared to with highlight info of diff
        """
        self._comparison = self.Comparison(self,ta=ta,tb=tb)
        if self.comparison_frame is None:
            self.comparison_frame = tk.Frame(self.root)
        self._comparison.a.pack(padx=5, pady=10, side=tk.LEFT)
        self._comparison.b.pack(padx=5, pady=20, side=tk.LEFT)

    def create_selection(self,text=None):
        """
        Create selection of list of text
        :param text: list of text to be selected from
        """
        self._selection = self.Selection(self,text=text)
        if self.selection_frame is None:
            self.selection_frame = tk.Frame(self.root)
        self._selection.selection.pack(padx=5,pady=10,side=tk.LEFT)

    def create_options(self,options=None):
        """
        Create option
        :param options: list of options that can be selected
        :return:
        """
        self._options = self.Option(self,options=options)
        if self.options_frame is None:
            self.options_frame = tk.Frame(self.root)
        self._options.options.pack()

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
                                command=lambda: callback(*kwargs[callback.__name__]))
        self.button.pack()

    def run(self):
        self.root.mainloop()
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

# ============= input box ============== #

def return_input(E1,top):
    global DEFAULT_LOCATION
    DEFAULT_LOCATION = E1.get()
    top.destroy()


def set_default_location(msg = ''):
    """
    Pop up a input entry
    :param msg: message to show
    :return: input
    """
    top = Tk()
    L1 = Label(top, text=msg)
    L1.pack(side=tk.LEFT)
    E1 = Entry(top, bd=5)
    E1.pack(side=tk.RIGHT)
    b = Button(top, text='okay', command=lambda: return_input(E1,top))
    b.pack(side='bottom')
    
    top.mainloop()
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
            line = line.replace('@','').replace('-','')
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

def is_location(location):
    """
    Check if location can be geocoded
    :param location: String representation of the Location Name
    :return: Boolean whther the location can be geocoded
    """
    return geolocator.geocode(location) is not None

# =========================Coref Utility Method======================== #

def stanford_pipeline(corpus, system = None):
    """
    This method call an external .jar routine to perform CoreNLP coreference
    # TODO: The difference between corefed and origin is not accurate. Please fix it.
    # 		Maybe consider fetch that information from the coref.java routine.
    """
    if not system:
        system = ['deterministic','statistical','neural']
    logger.info('Feed input file to StanfordPipeline...')
    tmp = os.getcwd()
    os.chdir(LIB)
    logger.warning('Switching to %s folder.', LIB)
    corefed_files = []
    conll_file = os.path.join(corpus.tmp_out,corpus.file_name+'conll.txt')
    # subprocess to execute stanford coref routine with 256mb    memory space
    for each in system:
        print(corpus.cleaned_path)
        subprocess.call(['java','StanfordPipeline',
                        '-fileName',corpus.file_name,
                        '-input', corpus.file_to_use,
                        '-outputDir', corpus.tmp_out,
                        '-system',each])
        out_path = os.path.join(corpus.tmp_out,corpus.file_name+"-"+each+"-corefed.txt")
        clean_up_file(file_name = corpus.file_name+"-"+each+'-corefed',
                      file_path = out_path,
                      tmp_out = corpus.tmp_out)
        corefed_files.append(out_path)
    os.chdir(tmp)
    logger.warning('Switching to %s folder.', tmp)
    return conll_file,corefed_files


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

    return origin_display, corefed_display



def wordnet_social_actor():
    logger.info('Extracting preliminary social actor list from WordNet')
    tmp = os.getcwd()
    os.chdir(LIB)
    logger.warning('Switching to %s folder.', LIB)
    subprocess.call(['java', 'ExtractSocialActors'])
    # TODO: mute java rountine print
    os.chdir(tmp)
    logger.info(
        'The verbose explaination of this social actor list can be found in social-actor-list-verbose.txt')
    f = open(os.path.join(LIB, 'social-actor-list.txt'), 'r')
    actors_list = f.read().split('\n')
    f.close()
    return actors_list

# ===================== Parser Tree Utility Method ======================= #

class ParentedTree(nltk.tree.ParentedTree):

    def __init__(self,*args,**kwargs):
        super(ParentedTree, self).__init__(*args,**kwargs)
        self.deprel = None

    def set_deprel(self,deprel):
        # set the depandency relationship for this node
        assert self.height() == 2
        self.deprel = deprel

    def get_index(self):
        assert self.height() == 2
        i = 0
        for each in self.root().subtrees(lambda t: t.height()==2):
            if each == self:
                return i
            i += 1
        return -1

    def get_deprel(self,tree):
        # request dependency rel from another tree in the same sentence
        assert self.height() == tree.height() == 2
        assert self.root() == tree.root()
        return self.deprel[tree.get_index()]

    def get_str(self):
        assert self.height() == 2
        return str(''.join(self.leaves()))


def read_tree(tree_representation):
    tree =  ParentedTree.fromstring(tree_representation)
    # tree.draw()
    return tree


def lemmatize(word,pos=None):

    return wnl.lemmatize(word,pos=pos)

# ================== Visualization Mehtod =================== #


def create_gexf(corpus):
    """
    Create gexf format file that can be used in Gephi to visualize result dynamically.
    :param corpus: A Corpus Object
    :return: gexf file path.
    """
    graph_name = corpus.file_name+".gexf"
    gexf = Gexf(corpus.file_name,"Author")
    graph = gexf.addGraph("directed","dynamic","SVO graph",timeformat="date")
    svo_result = corpus.svo_result
    with open(svo_result) as result:
        reader = csv.DictReader(result)

        for row in reader:
            if row["S"] not in graph.nodes:
                node = Node(graph,row["S"],row["S"],
                            r = random.randint(0,255),g = random.randint(0,255),b = random.randint(0,255),
                            size = "50",
                            spells = [
                                {"start":(EPOCH+datetime.timedelta(days = int(row["Sentence Index"])))
                                    .strftime("%Y-%m-%d"),
                                 "end":(EPOCH+datetime.timedelta(days = int(row["Sentence Index"])+1))
                                    .strftime("%Y-%m-%d")}
                            ])
                graph.nodes[row["S"]] = node

            else:
                graph.nodes[row["S"]].size = str(int(graph.nodes[row["S"]].size)+50)
                graph.nodes[row["S"]].spells.append({
                    "start": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"])))
                        .strftime("%Y-%m-%d"),
                    "end": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"]) + 1))
                        .strftime("%Y-%m-%d")
                })

            if row["O/A"] not in graph.nodes:
                node = Node(graph, row["O/A"], row["O/A"],
                            r=random.randint(0,255), g=random.randint(0,255), b=random.randint(0,255),
                            size="50",
                            spells=[
                                {"start": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"])))
                                    .strftime("%Y-%m-%d"),
                                 "end": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"]) + 1))
                                    .strftime("%Y-%m-%d")}
                            ])
                graph.nodes[row["O/A"]] = node

            else:
                graph.nodes[row["O/A"]].size = str(int(graph.nodes[row["O/A"]].size)+50)
                graph.nodes[row["O/A"]].spells.append({
                    "start": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"])))
                        .strftime("%Y-%m-%d"),
                    "end": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"]) + 1))
                        .strftime("%Y-%m-%d")
                })

            edge_id = row["S"]+" "+row["O/A"]
            if edge_id not in graph.edges:
                edge = Edge(graph,edge_id,row["S"],row["O/A"],
                            spells = [{"start": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"])))
                                    .strftime("%Y-%m-%d"),
                                       "end": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"]) + 1))
                                    .strftime("%Y-%m-%d")}],
                            label = row["V"])
                graph.edges[edge_id] = edge
            else:
                graph.edges[edge_id].spells.append(
                    {"start": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"])))
                                    .strftime("%Y-%m-%d"),
                     "end": (EPOCH + datetime.timedelta(days=int(row["Sentence Index"]) + 1))
                                    .strftime("%Y-%m-%d")})
    gexf.write(open(os.path.join(corpus.output_dir,graph_name),'wb'))
    return os.path.join(corpus.output_dir,graph_name)

def create_kml(corpus):
    """
    Create kml file that can be read by GoogleEarth and generate dynamic GoogleEarth Object
    :param corpus: A Corpus Object with SVO result already created
    :return: The path to the KML file
    """
    global DEFAULT_LOCATION
    kml = simplekml.Kml()
    with open(corpus.svo_result) as result:
        reader = csv.DictReader(result)
        if next(reader)["LOCATION"] == "":
            set_default_location("Please enter a default location: ")
        for line in reader:
            if line["LOCATION"] != "":
                DEFAULT_LOCATION = line["LOCATION"]
            print(DEFAULT_LOCATION,geolocator.geocode(DEFAULT_LOCATION).longitude)
            pnt = kml.newpoint(name = str(line["S"] + " "+ line["V"]+ " "+line["O/A"]))
            pnt.coords = [(geolocator.geocode(DEFAULT_LOCATION).latitude,
                          geolocator.geocode(DEFAULT_LOCATION).longitude)]
            pnt.timespan.begin = line["TIME_STAMP"]
            pnt.timespan.end = line["TIME_STAMP"]
    kml.save(os.path.join(corpus.output_dir,corpus.file_name+".kml"))
