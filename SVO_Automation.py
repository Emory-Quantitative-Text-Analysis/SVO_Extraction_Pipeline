import os
from util import *

# We will implement the whole pipeline using command line interface to support cross-platform usage 
# and minimize system dependencies

# ask for input_file_path
# sanity check and first-phase process to replace non-utf-8 characters,
# and seperate each complete sentence to lines
"""
display_coref('Murphy', TMP_OUT+'/Murphy/Murphy-cleanup.txt'\
	,[TMP_OUT+'/Murphy/Murphy-cleanup-out.txt',TMP_OUT+'/Murphy/Murphyneuralcorefed-cleanup.txt'],\
	['coref','neuralCoref'])
"""
while not CLEANED:

    INPUT_FILE_PATH = input('Please specify path of the text file you want to process:\n')
    
    try:
        INPUT_FILE = open(INPUT_FILE_PATH,'r')
        FILE_NAME = os.path.basename(INPUT_FILE_PATH)[:-4]
        OUTPUT = os.path.join(OUTPUT,FILE_NAME)
        TMP_OUT = os.path.join(TMP_OUT,FILE_NAME)
        # print(OUTPUT,TMP_OUT)
        if not os.path.isdir(OUTPUT):
            os.mkdir(OUTPUT)
        if not os.path.isdir(TMP_OUT):
            os.mkdir(TMP_OUT)
        _CLEANED_ORIGIN = clean_up_file(FILE_NAME,INPUT_FILE,TMP_OUT)
        # TODO: assertion of clean up format
        CLEANED = True
        INPUT_FILE.close()
        break

    except Exception as e:
        print('Invalid file cause an exceptiton ' + str(e))

while True:
	global COREFED
	COREF = input('Do you want to perform coreference resolution on your input file? (y/n)\n')
	if COREF.strip(' ') == 'y':
		COREFED = True # set corefed flag
		# initiate variables for the corefed results
		_CLEANED_COREFED = None
		_CLEANED_NEURAL_COREFED = None
		_COREFED_FILES = []
		_COREFED_APPROACHES = []

		while True:
			COREF_SYS = input('This pipeline provides two different coreference resolution system\n'+\
				'Type 1 for only Statistical System, Type 2 for only Neural System, Type 3 to compare two routines\n')
			
			if COREF_SYS.strip(' ') == '1':
				_CLEANED_COREFED = coref(FILE_NAME, _CLEANED_ORIGIN, TMP_OUT, System = 'statistical')
				_COREFED_FILES.append(_CLEANED_COREFED)
				_COREFED_APPROACHES.append('Statistical Coref')
				break

			elif COREF_SYS.strip(' ') == '2':
				_CLEANED_NEURAL_COREFED = coref(FILE_NAME,_CLEANED_ORIGIN,TMP_OUT, System = 'neural')
				_COREFED_FILES.append(_CLEANED_NEURAL_COREFED)
				_COREFED_APPROACHES.append('Neural Coref')
				break

			elif COREF_SYS.strip(' ') == '3':
				_CLEANED_COREFED = coref(FILE_NAME, _CLEANED_ORIGIN, TMP_OUT, System = 'statistical')
				_CLEANED_NEURAL_COREFED = coref(FILE_NAME,_CLEANED_ORIGIN,TMP_OUT, System = 'neural')
				_COREFED_FILES.append(_CLEANED_COREFED)
				_COREFED_FILES.append(_CLEANED_NEURAL_COREFED)
				_COREFED_APPROACHES.append('Statistical Coref')
				_COREFED_APPROACHES.append('Neural Coref')
				break
		print(_COREFED_APPROACHES,_COREFED_FILES)
		_CLEANED_COREFED_EDITED\
		= display_coref(FILE_NAME, _CLEANED_ORIGIN,_COREFED_FILES,_COREFED_APPROACHES)
		break

	elif COREF == 'n':
		_CLEANED_COREFED_EDITED = _CLEANED_ORIGIN # no coreference
		break 
	else:
		print('Invalid input')

while True:
	NER = input('Do you want to perform NER tagging so that Person\'s name and Location can be identified (y/n)?\n')
	if NER.strip(' ') == 'y':
		global NER_TAGGED
		NER_TAGGED = True
		logger.warn('Stanford NER Tagger may take a while, typically 2-3s per sentence.')
		#print(NER_TAGGED)
		break
	elif NER.strip(' ') == 'n':
		break
	else:
		print('Invalid Input \n')

_VERBOSE_OUT, _PATH_RAW_CSV, _PATH_CONCISE_CSV = \
clauseIE(FILE_NAME,_CLEANED_COREFED_EDITED,TMP_OUT, OUTPUT, NER_TAGGED = NER_TAGGED)

while True: 
	global SOCIAL_ACTOR_FILTERED
	MODE = input('Type 1 to use self-defined Social actors, 2 for WordNet-3.0 social actors, 3 for not using social actor filter \n')

	if MODE.strip(' ') == '1': # self-define mode
		SOCIAL_ACTOR_FILTERED = True
		_PATH_ACTORS = socialActor(1,_VERBOSE_OUT,TMP_OUT,NER_TAGGED = NER_TAGGED)	
		break

	elif MODE.strip(' ') == '2':
		print(NER_TAGGED)
		SOCIAL_ACTOR_FILTERED = True
		_PATH_ACTORS = socialActor(2,_VERBOSE_OUT,TMP_OUT, NER_TAGGED = NER_TAGGED)		
		break

	elif MODE.strip(' ') == '3':
		_PATH_ACTORS = socialActor(3,_VERBOSE_OUT,OUTPUT, NER_TAGGED = NER_TAGGED)
		break
	else:
		print('Invalid input')
		continue

while True:
	global DO_GEPHI
	MODE = input('Do you want to output dynamic graph? Gephi is required for this. (y/n) \n')
	if MODE.strip(' ') == 'y':
		DO_GEPHI = True
		break
	elif MODE.strip(' ') == 'n':
		DO_GEPHI = False
		break

while True:
	global DO_MAP
	MODE = input('Do you want to output a dyanmic Map? (y/n) \n')
	if MODE.strip(' ') == 'y':
		DO_MAP = True
		break
	elif MODE.strip(' ') == 'n':
		DO_MAP = False
		break

createResult(_PATH_ACTORS,FILE_NAME,_PATH_RAW_CSV,_PATH_CONCISE_CSV,TMP_OUT,OUTPUT,
	DO_GEPHI = DO_GEPHI, DO_MAP = DO_MAP)