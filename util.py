# coding: utf-8

# The utilities of SVO_Pipeline


# ======= System Level Dependency ====== #
import glob
import os
import sys
import subprocess
import time 
import datetime
import logging

# ======= Python Library ======== #
import string
import csv
import re
import string
from collections import Counter

# ====== External Library ======= #
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import StanfordNERTagger
from geopy.geocoders import Nominatim
import tkinter as tk
import difflib as df
import spacy
import pandas as pd
import folium

# TODO: Method Signature
# TODO: Add breakpoint at Gephi, Map etc.
# TODO: Work on the log information to make it more verbose
# TODO: Add time delay
# TODO: Integrate the map plot
# TODO: Reorganize the lib folder
# TODO: License
# TODO: GUI instruciton
# TODO: Install Requirement
# TODO: Rewrite Coref System choice
# TODO: Try drop ClauseIE 
# TODO: Rewrite Sentence Index
# TODO: Hihglight relative pornouns who where whom there so did etc..
# TODO: GUI for location (either provide change of location or use only where NER is provided) 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

#=======================Utility Variables===========================#

STARTING_DIR = os.getcwd() # scripts
LIB = os.path.join(STARTING_DIR,'../lib') # libraries and dependencies
OUTPUT = os.path.join(STARTING_DIR,'../output') # output dir
INPUT = os.path.join(STARTING_DIR,'../input') # input dir
TMP_OUT = os.path.abspath('../output/tmp/')# store any intermediate files
EPOCH = datetime.datetime.strptime('01/01/1970',"%m/%d/%Y")

INPUT_FILE = None
INPUT_FILE_PATH = None
FILE_NAME = None
SENTENCES = None

# ====== Flags ====== #
NER_TAGGED = False
CLEANED = False
COREFED = False
SOCIAL_ACTOR_FILTERED = False

DO_GEPHI = False
DO_MAP = False
# ====== Models ====== #
sys.path.insert(0,'../lib/neuralcoref')
from neuralcoref import Coref 
MODEL = os.path.join(LIB,'./en_core_web_sm/en_core_web_sm-2.0.0/') # trained English model for neuralcoref
nlp = spacy.load(MODEL) # load the en model

NER_MODEL = os.path.join(LIB,'./edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz')
NER_JAR = os.path.join(LIB,'./edu/stanford/stanford-ner.jar')
ner_tagger = StanfordNERTagger(NER_MODEL,NER_JAR)
LOCATION_LIST = [] # global var to hold location info, need to keep the sentence index
PERSON_SET = set() # global var to hold person info, no need to keep sentence index

geolocator = Nominatim()
# TODO: Merging file methods

# -*- coding: utf-8 -*-

# ============================= Split Sentence Utility Method ========================= #
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

# ======================Clean Up Utility Method======================#
def clean_up_file(_FILE_NAME, _FILE, _PATH_OUT):
	"""
	Clean up and join the lines, return cleanedup file path.
	# TODO: Interview Format
	"""
	logger.info('Cleaning up ...')
	_PATH_CLEAN = os.path.join(_PATH_OUT, _FILE_NAME+'-cleanup.txt')
	with open(_PATH_CLEAN, 'w') as out:
		lines = split_into_sentences(_FILE.read())
		for line in lines:
			line = line.replace('Q:','').replace('A:','')
			line = line.replace(u"â $ ™", "'").replace(u"â€™","'")
			line = line.replace(u'â $', '').replace(u'œ', '').replace("''", '').replace("``", '')
			line = line.replace(u"¦", '').replace(u"™", '').strip()
			print(line)
			line = ''.join(filter(lambda x: x in string.printable or x == '\'',line))
			print(line)
			if isSentence(line):
				out.write(line)
				out.write('\n') # join the lines
	return _PATH_CLEAN

def isSentence(sentence):
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


def isTitle(sentence):
	"""
	Check if a line is title. 
	"""
	if sentence[-1] not in string.punctuation:
		if len(sentence) < Title_length_limit:
			# print sentence
			return True
	if sentence.isupper():
		# print sentence
		return True
	if sentence.istitle():
		# print sentence
		return True
# ========================== NER Tagger Utility Method ========================= #

def NER_tag_sentence(sentence):
	while 'JAVAHOME' not in os.environ:
		java_path = input(
			'NER Tagger require the JAVAHOME path to be set, please specify your java.exe file path. Typically it\'s \
			some where like C:/Program Files/Java/jdk1.8.0_161/bin/java.exe, please use backslash in path:\n'
			)
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


def tag_PERSON_LOCATION(sentence_index, sentence, _PERSON_SET, _LOCATION_LIST):
	tag = NER_tag_sentence(sentence)
	print(sentence,tag)
	PERSONs = list(filter(lambda x: x[1] == 'PERSON', tag))
	LOCATIONs = list(filter(lambda x: x[1] == 'LOCATION', tag))
	_LOCATION_LIST.append(LOCATIONs)
	_PERSON_SET.update([x[0] for x in PERSONs])


#=========================Coref Utility Method========================#
def neuralCoref(_FILE_NAME, _CLEANED_ORIGIN, _TMP_OUT):
	"""
	This method uses the neuralCoref library to perform coreference,
	generally speaking, this usually gave better result than the CoreNLP approach
	"""
	logger.info('Neural Coreferencing...')
	coref = Coref()
	_NEURAL_COREFED = _TMP_OUT+'\\'+_FILE_NAME+'-neuralcorefed.txt'
	sentences = split_into_sentences(open(_CLEANED_ORIGIN,'r',encoding='utf-8',errors="ignore").read())
	coref.continuous_coref(utterances = sentences)
	out = open(_NEURAL_COREFED,'w')
	out.write('\n'.join(coref.get_resolved_utterances()))
	out = open(_NEURAL_COREFED,'r') # switch to read mode for clean-up
	_CLEANED__NEURAL_COREFED = clean_up_file(_FILE_NAME+'-neuralcorefed'
		,out,_TMP_OUT)
	return _CLEANED__NEURAL_COREFED


def coref(_FILE_NAME, _CLEANED_ORIGIN, _TMP_OUT, System = 'statistical'):
	"""
	This method call an external .jar routine to perform CoreNLP coreference
	# TODO: The difference between corefed and origin is not accurate. Please fix it. 
	# 		Maybe consider fetch that information from the coref.java routine. 
	"""
	logger.info('Coreferencing...')
	os.chdir(os.path.abspath('../lib'))
	print(System)
	subprocess.call(['java', 'Coref', 
		'-inputFile', _CLEANED_ORIGIN, 
		'-outputDir', _TMP_OUT,
		'-system',System])

	_COREFED_FILE = open(_CLEANED_ORIGIN[:-4]+"-"+System+'-out.txt')
	_CLEANED_COREFED = clean_up_file(_CLEANED_ORIGIN[:-4]+"-"+System,_COREFED_FILE,_TMP_OUT)
	os.chdir(STARTING_DIR)

	return _CLEANED_COREFED


def display_coref(_FILE_NAME,_CLEANED_ORIGIN, _COREFED_FILES=[], _COREFED_APPROACHES = []):

	try: # assert every coref approach must correspond to one corefed file
		assert len(_COREFED_APPROACHES) == len(_COREFED_FILES)
	except AssertionError as e:
		logger.debug('Every coref approach must correspond to one corefed file')

	corefed_edited_results = [] # temporary hold the corefed and edited results
	_enum = ''
	_CLEANED_COREFED_EDITED = os.path.join(TMP_OUT,
			_FILE_NAME+'-cleaned-corefed-edited.txt')

	for i, each in enumerate(_COREFED_APPROACHES):
		_enum += str(i) + ' : '+_COREFED_APPROACHES[i]+'\n' 

	def finishCallBack(GUI):

		edited = GUI.corefed.get('1.0',tk.END)
		corefed_edited_results.append(edited)
		GUI.root.destroy()

	class corefGUI:

		def __init__(self,COREFED_FILE,_COREFED_APPROACHE):
			self.root = tk.Tk()
			self.root.title(_COREFED_APPROACHE)

		def create_text(self,origin_display,corefed_display):

			self.origin = tk.Text(self.root)

			for i in range(len(origin_display)):
				each = origin_display[i]
				self.origin.insert(tk.INSERT,each[0]+'\n')

				for highlight in each[1]:
					self.origin.tag_add("here", str(i+1)+"."+str(highlight[0]), 
						str(i+1)+"."+str(highlight[1]))
					self.origin.tag_config("here", background="yellow", foreground="blue")
			
			self.origin.pack(padx=5, pady=10, side=tk.LEFT)

			self.corefed = tk.Text(self.root)

			for i in range(len(corefed_display)):
				each = corefed_display[i]
				self.corefed.insert(tk.INSERT,each[0]+'\n')

				for highlight in each[1]:
					self.corefed.tag_add("here", str(i+1)+"."+str(highlight[0]), 
						str(i+1)+"."+str(highlight[1]))	
					self.corefed.tag_config("here", background="red", foreground="blue")

			self.corefed.pack(padx=5, pady=20, side=tk.LEFT)

		def create_button(self):
			finish_button = tk.Button(self.root,text="Finish",
				command = lambda: finishCallBack(self))
			finish_button.pack()

	origin_file = open(_CLEANED_ORIGIN)
	origin_text = origin_file.read()

	for index in range(0,len(_COREFED_FILES)):

		# Prepare content for GUI display

		origin_sentences = split_into_sentences(origin_text) # reinitiate the origin sentences
		corefed_file = open(_COREFED_FILES[index])
		corefed_text = corefed_file.read()
		corefed_sentences = split_into_sentences(corefed_text)
		corefed_file.close()

		edit_coref = None
		# Prepare varaibles for GUI display

		# print(corefed_sentences, origin_sentences)
		origin_display = []
		corefed_display = []

		"""
		SequenceMatcher gave mathing point for each sentences;
		We use this to find the difference.
		"""
		for i in range(0,min(len(corefed_sentences),len(origin_sentences))):

			origin_display_highlighted = []
			corefed_display_highlighed = []

			origin_len = 0
			corefed_len = 0

			# mark junk characters " ' tab and space
			s = df.SequenceMatcher(lambda x: x in " \'\t\"", 
				origin_sentences[i], corefed_sentences[i],autojunk=False)
			matching = s.get_matching_blocks()

			for j in range(0,len(matching)-1):

				start = matching[j]
				end = matching[j+1]

				origin_display_highlighted.append((start[0]+start[2]+origin_len,
					end[0]+origin_len))
				corefed_display_highlighed.append((start[1]+start[2]+corefed_len,
					end[1]+corefed_len))

			origin_len += end[0]
			corefed_len += end[1]
			
			origin_display_tuple = (origin_sentences[i],
				origin_display_highlighted)

			corefed_display_tuple = (corefed_sentences[i],
				corefed_display_highlighed)

			origin_display.append(origin_display_tuple)
			corefed_display.append(corefed_display_tuple)

		#======Edit Corefed=====#
		logger.info('Editing '+_COREFED_APPROACHES[index])
		edit_coref = corefGUI(_COREFED_FILES[index],_COREFED_APPROACHES[index])
		edit_coref.create_text(origin_display,corefed_display)
		edit_coref.create_button()
		edit_coref.root.mainloop()

	while True:
		_COREF_CHOICE = input('Which coref approach do you want to use? Please type in the index.\n'+_enum)
		try:
			with open(_CLEANED_COREFED_EDITED,'w') as out:
				out.write('.\n'.join(
					split_into_sentences(corefed_edited_results[int(_COREF_CHOICE.strip(' '))])))
			break
		except Exception as e:
			print('Invalid because' + str(e))

	return _CLEANED_COREFED_EDITED


#=========================== SVO Extraction Utility Method ====================# 

def clauseIE(_FILE_NAME, _CLEANED_COREFED_EDITED, _TMP_OUT, _OUT, NER_TAGGED = False):
	# ========== Index Sentence========#
	logger.info("Indexing sentences...")
	_CLEANED_COREFED_EDITED_INDEXED = os.path.join(_TMP_OUT,
		_FILE_NAME+'-cleaned-corefed-edited-indexed.txt')

	with open(_CLEANED_COREFED_EDITED, 'r') as f:
		sentences = f.read()
		sentences = split_into_sentences(sentences)
		with open(_CLEANED_COREFED_EDITED_INDEXED,'w') as out:
			print(NER_TAGGED)
			if NER_TAGGED:
				# locf = open('locations.txt','w')
				logger.info('NERtagging while indexing ... ')
				for i,sentence in enumerate(sentences):
					# print(sentence)
					"""
					locf.write(EPOCH+datetime.timedelta(days=i)).strftime("%m/%d/%Y")
					locf.write(EPOCH+datetime.timedelta(days=i+1)).strftime("%m/%d/%Y")
					locf.write()
					"""
					out.write('%d\t%s\n'% (i, sentence))
					tag_PERSON_LOCATION(i,sentence,PERSON_SET,LOCATION_LIST) 
					print(PERSON_SET, LOCATION_LIST)
			else:
				for i,sentence in enumerate(sentences):
					# print(sentence)
					out.write('%d\t%s\n'% (i, sentence))


	# ========== Feed to ClauseIE ==========#
	
	logger.info('Feeding to ClauseIE....')

	os.chdir(os.path.join(LIB,'clauseIE'))
	# grab output
	_VERBOSE_OUT = os.path.join(_TMP_OUT,_FILE_NAME+'-verbose_out.txt')
	subprocess.call(['java', '-jar', 'clausie.jar', 
		'-vlf', _CLEANED_COREFED_EDITED_INDEXED, '-o', _VERBOSE_OUT,'-s'])
	os.chdir(STARTING_DIR)
	
	# TODO: This is not optimal, if anyone wants to modify this code, please fix.
	#		Ideally, we will refer to Hang's utility scripts, but all work is done here
	#		Below is Gabriel Wang's modification
	# Declare output pathes and other variables
	_PATH_RAW_SVO = os.path.join(_TMP_OUT, 'raw_svo.txt')
	_PATH_RAW_CSV = os.path.join(_OUT,'raw_svo.csv')
	_PATH_CONCISE_SVO = os.path.join(_TMP_OUT,'concise_svo.txt')
	_PATH_CONCISE_CSV = os.path.join(_OUT,'concise_svo.csv')

	matchobj = []
	concise_matchobj = []

	with open(_VERBOSE_OUT) as f:
		content = f.read()
		lines = content.split('\n')
		for line in lines:
			if re.match(r'[0-9]+\s',line):
				if len(line.split('\t')) != 4: # SV, use NaN for O
					line+='\tNaN'
				matchobj.append(line.replace('"',''))

		# =========The below part was originally from Hang Jiang========# 

		concise_matchobj = re.findall(r'SV.* \((.*)\)', content)
		concise_out = '\n'.join(concise_matchobj)
		r = re.compile('@\d*')
		concise_out = r.sub('',concise_out)
		# remove irrelevant labels: only reserve S,V,O
		concise_out = re.sub(r'IO: \w*,?', '', concise_out)
		concise_out = re.sub(r'A[\?\!\-]: \w*,?', '', concise_out) # remove A-, A?, A!
		concise_out = re.sub(r'.COMP: \w*,?', '', concise_out) # remove .COMP
		concise_out = re.sub(r'IO: \w*,?', '', concise_out)

		# ========Up till here===========#

	with open(_PATH_RAW_SVO,'w') as output:
		output.write('\n'.join(matchobj))

	with open(_PATH_CONCISE_SVO,'w') as output:
		output.write(concise_out)

	# Open files for writting
	raw_csv = open(_PATH_RAW_CSV,'w',newline='')
	concise_csv = open(_PATH_CONCISE_CSV,'w',newline='')

	# Register csv writers
	fieldnames = ['Sentence ID','S','Relation','O']

	raw_writer = csv.DictWriter(raw_csv,fieldnames=fieldnames)
	raw_writer.writeheader()

	concise_writer = csv.DictWriter(concise_csv,fieldnames=fieldnames[1::])
	concise_writer.writeheader()

	# Process raw svo object
	with open(_PATH_RAW_SVO,'r') as raw_svo:
		while raw_svo:
			line = raw_svo.readline().rstrip().split('\t')
			if len(line) >= 3:
				raw_writer.writerow({
						'Sentence ID':line[0],
						'S':line[1],
						'Relation':line[2],
						'O':line[3]
					})
			else:
				raw_csv.close()
				break # eof

	# Process concise svo object
	with open(_PATH_CONCISE_SVO,'r') as concise_svo:
		while concise_svo:
			line = re.sub(r'[^a-zA-Z0-9,:]+','',concise_svo.readline()).split(',')
			line_dic = {'O':' '}
			if len(line) >=2:
				for each in line:
					if not each:
						continue
					if each[0].rstrip() == 'S':
						line_dic['S'] = each[2::]
					elif each[0].rstrip() == 'V':
						line_dic['Relation'] = each[2::]
					else:
						line_dic['O'] = each[2::]
				concise_writer.writerow(line_dic)
			else:
				concise_csv.close()
				break #eof

	return _VERBOSE_OUT, _PATH_RAW_CSV, _PATH_CONCISE_CSV

# ======================== Social Actor Filter Utility Method ================== #

def find_NN_list(_VERBOSE_OUT):
	# Extract all NN  from the verbose output of cluaseIE
	with open(_VERBOSE_OUT,'r') as f:
		content = f.read()
		NN_list = set(re.findall(r'[\s\[\:]+(\w+)/NN', content))
	return NN_list

def find_NNP_list(_VERBOSE_OUT):
	# Extract all NNP  from the verbose output of cluaseIE
	with open(_VERBOSE_OUT,'r') as f:
		content = f.read()
		NNP_list = set(re.findall(r'[\s\[\:]+(\w+)/NNP', content))
	return NNP_list

def find_social_actors(actors_list,_VERBOSE_OUT, NER_TAGGED = False):

	NN_list = find_NN_list(_VERBOSE_OUT)
	if NER_TAGGED:
		social_actors = PERSON_SET
	else:
		social_actors = set()
	lmtzr = WordNetLemmatizer()
	for each in NN_list:
		if lmtzr.lemmatize(each) in actors_list:
			social_actors.add(each)
	return social_actors

def socialActor(MODE,_VERBOSE_OUT,_OUT,NER_TAGGED = False):
	"""
	This method switched on the Social Actor filter Mode chosen by the user
	and compare the NNs to the actor list to return a list of social actors in the file
	appeared in Subject and Objects
	"""

	#========== Social Agent GUI ========#
	_PATH_ACTORS = os.path.join(_OUT, 'actors.txt')
	if MODE == 1: #self-defined
		logger.info('Define your own social actor list')
		actors_list =[]

	elif MODE == 2:

		logger.info('Extracting preliminary social actor list from WordNet')
		os.chdir(LIB)
		subprocess.call(['java', 'ExtractSocialActors'])
		# TODO: mute java rountine print
		os.chdir(STARTING_DIR)
		logger.info('The verbose explaination of this social actor list can be found at ../lib/social-actor-list-verbose.txt')
		f = open(os.path.join(LIB,'social-actor-list.txt'),'r')
		actors_list = f.read().split('\n')
		f.close()

	elif MODE == 3:

		logger.info('Not using filters')
		f = open(_PATH_ACTORS,'w') # make sure to erase everything
		f.close()

		# TODO: Check if this is correct, I doubt
		return _PATH_ACTORS # return an empty actor list

	logger.info('Adding social actors...')
	# print(actors_list)
	# ======= Callback Functions for GUI ======== #
	edited = ''
	def editCallBack(GUI):
		edited = GUI.list.get('1.0',tk.END)
		actor_list = edited.split('\n')
		GUI.edit_button.destroy()
		GUI.filter_button.pack()

	def finishCallBack(GUI):
		social_actors = GUI.actors.get('1.0',tk.END)
		with open(_PATH_ACTORS,'w') as out:
			out.write(social_actors)
		GUI.root.destroy()

	def filterCallBack(GUI):
		logger.info('Editing social actors from the file...')
		social_actors = find_social_actors(actors_list,_VERBOSE_OUT,NER_TAGGED = NER_TAGGED)
		GUI.display_filtered(social_actors)
		if NER_TAGGED:
			GUI.compare_location(LOCATION_LIST)
		GUI.finish_button = tk.Button(GUI.bottom_frame, text = "Finish",
			command=lambda: finishCallBack(GUI))
		GUI.finish_button.pack()
		GUI.filter_button.destroy()
		GUI.message()
		# GUI.root.destroy() # exist GUI
	class socialActorGUI():

		def __init__(self,actors_list = []):
			self.root = tk.Tk()
			self.root.title('WordNet-3.0 Social Actor List')
			self.bottom_frame = tk.Frame(self.root)
			self.bottom_frame.pack(side = tk.BOTTOM)

			self.create_text(actors_list)
			self.create_button()

		def create_text(self,actors_list):
			self.list_label = tk.Label(self.root,text = 'WordNet Actor List')
			self.list_label.pack(padx = 30, pady = 10, side=tk.LEFT)
			self.list = tk.Text(self.bottom_frame,width= 20)
			self.list.insert(tk.INSERT,'\n'.join(actors_list))
			self.list.pack(padx=5, pady=10, side=tk.LEFT)

		def compare_location(self,location_list):
			self.location_label = tk.Label(self.root,text = 'NER Locations')
			self.location_label.pack(padx = 25, pady = 10, side=tk.LEFT)
			self.locations = tk.Text(self.bottom_frame, width = 20)
			for each in location_list:
				if not each == []:
					for e in each:
						self.locations.insert(tk.INSERT,e[0]+'\n')
			self.locations.pack(padx=5,pady=10,side=tk.LEFT)

		def display_filtered(self,social_actors):
			self.filtered_label = tk.Label(self.root,text = 'Actors Detected in the Text')
			self.filtered_label.pack(padx = 25, pady = 10, side=tk.LEFT)
			self.actors = tk.Text(self.bottom_frame, width = 20)
			self.actors.insert(tk.INSERT,'\n'.join(social_actors))
			self.actors.pack(padx=5,pady=10,side=tk.LEFT)

		def create_button(self):
			logger.info('Editing actors list...')
			self.filter_button = tk.Button(self.bottom_frame, text = "Filter",
				command=lambda: filterCallBack(self))
			self.edit_button = tk.Button(self.bottom_frame, text="Finish Editing",
				command = lambda: editCallBack(self))
			self.edit_button.pack()

		def message(self):
			tk.messagebox.showinfo("Tip","Please use Locations to refine Actors Detected.")

		# TODO: message instruciton
	GUI = socialActorGUI(actors_list = actors_list)
	GUI.root.mainloop()

	return _PATH_ACTORS


def selectActorsToUse(_PATH_ACTORS):
	"""
	Return a list of actors to create Gephi
	"""
	with open(_PATH_ACTORS,'r') as f:
		social_actors = f.read().split('\n')

	actors_to_use = []

	def selectCallBack(GUI):
		for each in GUI.list.curselection():
			actors_to_use.append(social_actors[each])
		GUI.root.destroy()

	def allCallBack(GUI):
		nonlocal actors_to_use
		actors_to_use = social_actors[::] # use all social actors contained
		GUI.root.destroy()

	def noneCallBack(GUI):
		GUI.root.destroy()

	class chooseActorGUI():

		def __init__(self,social_actors = []):
			self.root = tk.Tk()
			self.root.title('Social Actor List Matched with WordNet Social Actor List')
			self.bottom_frame = tk.Frame(self.root)
			self.bottom_frame.pack(side = tk.BOTTOM)
			self.create_text(social_actors)
			self.create_button()

		def create_text(self,actors_list):

			self.list = tk.Listbox(self.bottom_frame,selectmode=tk.MULTIPLE)
			for i in range(len(social_actors)):
				self.list.insert(i+1,social_actors[i])
			self.list.pack(padx=5, pady=10, side=tk.LEFT)

		def create_button(self):
			all_button = tk.Button(text='Select All',
				command = lambda: allCallBack(self))
			all_button.pack()

			select_button = tk.Button(text='Select Items',
				command = lambda: selectCallBack(self))
			select_button.pack()

			none_button = tk.Button(text='Select None',
				command = lambda: noneCallBack(self))
			none_button.pack()


	GUI = chooseActorGUI(social_actors = social_actors)
	GUI.root.mainloop()

	return actors_to_use

def createResult(_PATH_ACTORS,FILE_NAME,_PATH_RAW_CSV,_PATH_CONCISE_CSV,_TMP_OUT,_OUTPUT,DO_GEPHI = False, DO_MAP = False ):
	global SOCIAL_ACTOR_FILTERED
	if SOCIAL_ACTOR_FILTERED:
		actors_to_use = selectActorsToUse(_PATH_ACTORS)
	else:
		actors_to_use = []
	if actors_to_use == []:
		SOCIAL_ACTOR_FILTERED = False # this is for select none mode in 
	# print(actors_to_use)
	#========= Output SVO csv files filtered by actors_to_use==========#
	filtered_raw_csv = open(os.path.join(_OUTPUT,'filtered_raw.csv'),'w',newline='')
	fieldnames = ['Sentence ID','S','Relation','O']
	filtered_raw_writer = csv.DictWriter(filtered_raw_csv,fieldnames=fieldnames)
	filtered_raw_writer.writeheader()
	with open(_PATH_RAW_CSV, 'r',newline='') as raw_svo:
		raw_reader = csv.reader(raw_svo)
		for row in raw_reader:
			for cell in row[1::]:
				for word in cell:
					if not SOCIAL_ACTOR_FILTERED or word in actors_to_use:
						filtered_raw_writer.writerow({
							'Sentence ID':row[0],
							'S':row[1],
							'Relation':row[2],
							'O':row[3]
							})

	#=========Filter the concise SVO and prepare for Gephi===========#
	"""
	 Table can have the following fields:
            Node1Label; Node2Label; EdgeLabel; StartDateNode1; StartDateNode2; EdgeDate; EndDateNode1; EndDateNode2; Node1Size; Node2Size; EdgeThickness

            Required Entries are:
            Node1Label; Node2Label

            Dates must be in format: MM/dd/yyy

            If StartDates are given and no endDates are given then:
                the algorithm will assume that EndDate of all object = StartDate + 1
            If StartDates and EndDates are both given then:
                ...obvious...
            If no dates are given then:
                the algorithm will create a static graph
            If no edgeDate is given then:
                the edge will disappear as soon as one of the nodes he is connecting disappears
    """
	filtered_concise_csv = open(os.path.join(_OUTPUT,'filtered_concise.csv'),'w',newline='')
	fieldnames = ['Sentence ID','S','Relation','O']
	filtered_concise_writer = csv.DictWriter(filtered_concise_csv,fieldnames=fieldnames)
	filtered_concise_writer.writeheader()
	if DO_GEPHI:
		gephi_data = {
			'Node1Label':[],
			'Node2Label':[],
			'EdgeLabel':[],
			'StartDateNode1':[],
			'StartDateNode2':[],
			'EdgeStartDate':[],
			'EdgeEndDate':[],
			'EndDateNode1':[],
			'EndDateNode2':[],
			'Node1Size':[],
			'Node2Size':[],
			'EdgeThickness':[],
		}

	if DO_MAP:
		map_data = {}

	with open(_PATH_CONCISE_CSV,'r',newline='') as filtered_concise:
		concise_reader = csv.reader(filtered_concise)
		sentence_index = 0
		for row in concise_reader:
			if not SOCIAL_ACTOR_FILTERED or row[0] in actors_to_use or row[2] in actors_to_use:
				filtered_concise_writer.writerow({
					'Sentence ID':sentence_index,
					'S':row[0],
					'Relation':row[1],
					'O':row[2]
					})
				if DO_GEPHI:
					gephi_data['Node1Label'].append(row[0])
					gephi_data['Node2Label'].append(row[1])
					gephi_data['EdgeLabel'].append(row[2])
					gephi_data['EdgeStartDate'].append(
						(EPOCH+datetime.timedelta(days=sentence_index)).strftime("%m/%d/%Y"))
					gephi_data['EdgeEndDate'].append(
						(EPOCH+datetime.timedelta(days=sentence_index+1)).strftime("%m/%d/%Y"))

			sentence_index += 1
			"""
			gephi_data['StartDateNode1'].append(
				(EPOCH+datetime.timedelta(days=sentence_index)).strftime("%m/%d/%Y"))
			gephi_data['StartDateNode2'].append(
				(EPOCH+datetime.timedelta(days=sentence_index)).strftime("%m/%d/%Y"))
			gephi_data['EdgeDate'].append(
				(EPOCH+datetime.timedelta(days=sentence_index)).strftime("%m/%d/%Y"))
			
			gephi_data['StartDateNode1'].append(
				(EPOCH+datetime.timedelta(days=0)).strftime("%m/%d/%Y"))
			gephi_data['StartDateNode2'].append(
				(EPOCH+datetime.timedelta(days=0)).strftime("%m/%d/%Y"))
			gephi_data['EndDateNode1'].append(
				(EPOCH+datetime.timedelta(days=0)).strftime("%m/%d/%Y"))
			gephi_data['EndDateNode1'].append(
				(EPOCH+datetime.timedelta(days=0)).strftime("%m/%d/%Y"))
			for i in range(len(gephi_data['EndDateNode1'])):
				gephi_data['EndDateNode1'][i] = EPOCH+datetime.timedelta(days=sentence_index+1).strftime("%m/%d/%Y")
				gephi_data['EndDateNode2'][i] = EPOCH+datetime.timedelta(days=sentence_index+1).strftime("%m/%d/%Y")
			"""
	for each in gephi_data['Node1Label']:
		gephi_data['Node1Size'].append(str(gephi_data['Node1Label'].count(each)))
	for each in gephi_data['Node2Label']:
		gephi_data['Node2Size'].append(str(gephi_data['Node2Label'].count(each)))
	for each in gephi_data['EdgeLabel']:
		gephi_data['EdgeThickness'].append(str(gephi_data['EdgeLabel'].count(each)))
	# print(gephi_data)
	if DO_GEPHI:
		with open(os.path.join(_TMP_OUT,'tmpData.csv'),'w') as tmp_data:
			for i in range(len(gephi_data['Node1Label'])):
				tmp_data.write(
					gephi_data['Node1Label'][i]+';'+\
					gephi_data['Node2Label'][i]+';'+\
					gephi_data['EdgeLabel'][i]+';'+\
					#(EPOCH+datetime.timedelta(days=0)).strftime("%m/%d/%Y")+';'+\
					#(EPOCH+datetime.timedelta(days=0)).strftime("%m/%d/%Y")+';'+\
					gephi_data['EdgeStartDate'][i]+';'+\
					gephi_data['EdgeStartDate'][i]+';'+\
					gephi_data['EdgeStartDate'][i]+';'+\

					gephi_data['EdgeEndDate'][i]+';'+\
					gephi_data['EdgeEndDate'][i]+';'+\
					gephi_data['EdgeEndDate'][i]+';'+\
					#(EPOCH+datetime.timedelta(days=sentence_index)).strftime("%m/%d/%Y")+';'+\
					#(EPOCH+datetime.timedelta(days=sentence_index)).strftime("%m/%d/%Y")+';'+\
					gephi_data['Node1Size'][i]+';'+\
					gephi_data['Node2Size'][i]+';'+\
					gephi_data['EdgeThickness'][i]+';'
					)
				tmp_data.write('\n')
		os.chdir(LIB)
		subprocess.call(['java', '-jar', 'GephiGraphCreator.jar',
		 os.path.join(_TMP_OUT,'tmpData.csv'),'0','1','2','3','4','5','6','7','8','9','10','11',os.path.join(_OUTPUT,'Gephi.gexf')])
	
	return filtered_raw_csv,filtered_concise_csv

	"""
	_PATH_FILTERED_CSV = os.path.join(_OUT,'filtered.csv')
	_PATH_FILTERED_CONCISE_CSV = os.path.join(_OUT,'filtered_concise.csv')

	fieldnames = ['Sentence ID','S','Relation','O']
	
	filtered_csv = open(_PATH_FILTERED_CSV,'w',newline='')
	filtered_writer = csv.DictWriter(filtered_csv,fieldnames=fieldnames)
	filtered_writer.writeheader()

	filtered_concise_csv = open(_PATH_FILTERED_CONCISE_CSV,'w',newline='')
	filtered_concise_writer = csv.DictWriter(filtered_concise_csv,fieldnames=fieldnames[1::])
	
	result_list = set()
	concise_result_list = set()

	with open(os.path.join(TMP_OUT,'raw_svo.txt'), 'r') as raw_svo: # TODO: get rid of the arbitrary file name
		while raw_svo:
			line = raw_svo.readline().rstrip().split('\t')
			if len(line) >= 3:
				for word in (line[1]+' '+line[3]).split(' '):
					if word.lower() in [ x.lower() for x in actors_list] and word !='NaN':
						result_list.add(word)
						print(word)
						filtered_writer.writerow({
							'Sentence ID':line[0],
							'S':line[1],
							'Relation':line[2],
							'O':line[3]
							})
						break
			else:
				filtered_csv.close()
				break # eof
	with open(_PATH_CONCISE_CSV, 'r') as concise_csv:
		concise_csv.readline() # skip the column names
		while concise_csv:
			line = concise_csv.readline()[:-1].split(',') # the delimeter is a comma for this csv file, trim the newline
			if len(line) < 2:
				filtered_concise_csv.close()
				break # eof
			for word in line:
				if word.lower() in [x.lower() for x in actors_list]:
					# print(line)
					concise_result_list.add(word)
					filtered_concise_writer.writerow({
						'S':line[0],
						'Relation':line[1],
						'O':line[2],
						})
					break
	"""	
