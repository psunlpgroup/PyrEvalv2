import os
import sys
import shutil
from subprocess import call
#Wasih (02-19-20) Use functions instead of calling script
from splitsent import *
from Stanford.stanford import *
from Pyramid.pyramid import pyramidmain

#for randomly generating list
from random import sample

#Wasih (02-26-20) Make conditional imports depending on Python version
#Wasih (02-27-20) Define a variable for python version & then use it
PYTHON_VERSION = 2
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser
    PYTHON_VERSION = 3

#Wasih (02-21-20) Use termcolor to display colored text
from termcolor import colored

#Wasih (02-27-20) Use imports of traceback and logging to print any exception
import logging
import traceback

#Adithya Importing preprocess as a function
# from Preprocess import preprocess_mongo_min as preprocess_functions
from Preprocess import preprocess_mongo_min as preprocess_functions

#Adithya Importing scoring as a function
from Scoring import scoring_mongo_maj as scoring_functions

#Importing for MongoDB Operations
from MongoDB import mongo_db_functions
from MongoDB import pyramid_operations_mongo_new

#Variables for MongoDB
#TODO: to fetch from parameters files
db_conn = "mongodb://localhost:27017"
database_name = 'PYREVAL_TEST_DB';
mongodb_operations = mongo_db_functions.MongoDB_Operations(db_conn)

#Code to connect to the databse
mongodb_operations.connect(database_name)

#Importing Error Object for handling Intermmediate Data
from Error_Operations import error_operations_mongo_new

#Variables for Handling Intermmediate Data and Errors
error_operations_obj = error_operations_mongo_new.error_object()

#To maintain globally
from MongoDB.Models import Student_Essay_Model 


INPUT_STR = '>>> '

INSTRUCTIONS = """
Welcome to the PyrEval Launcher.

NOTES:
- The Stanford Core NLP Tools package should be in ./Stanford/

a: Run all functions

1: Preprocess - Split sentences
2: Run Stanford Core NLP Tools
3: Preprocess - Main
4: Score pyramids

c: Clean directories
i: Change python interpreter

To quit, type q.
"""
#Wasih (02-21-21) more convenient quitting

def autorun():
    splitsent()
    stanford()
    preprocess()
    score()


def splitsent():

    try:
        #Wasih (02-21-21) Check for split directory present or not, if not then create it
        if not os.path.exists(split_peer_dir):
            os.makedirs(split_peer_dir)
        
        if not os.path.exists(split_model_dir):
            os.makedirs(split_model_dir)
        
        #changed for mongoDB operations
        split(raw_peer_dir, split_peer_dir, mongodb_operations, student_metadata_obj)
        # split(raw_model_dir, split_model_dir, mongodb_operations, student_metadata_obj)

        text = colored('\n\n********************Splitting of Sentences/normalization completed!********************\n\n', 'green', attrs = ['bold'])
        print (text)

        error_operations_obj.sent_split_stage = 'Sentence Splitting Complete'
        
    except Exception as e:
        text = colored('\n\n********************Splitting of Sentences/normalization Threw an Error!********************\n\n', 'red', attrs = ['bold'])
        logging.error(traceback.format_exc())
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        #print(e)
        print (text)
    
def stanford():
    os.chdir(stanford_dir)
    
    #Wasih (02-19-21) Use functions instead of calling script
    try:
        try:
            stanfordmain(split_peer_dir, 1, dynamic_base_dir, seg_method)
            error_operations_obj.stanford_core_nlp_stage = 'Stanford corenlp xml output complete'
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Stanford Pipelining of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            print (text)
            error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        os.chdir(stanford_dir)
        try:
            stanfordmain(split_model_dir, 2, dynamic_base_dir, seg_method)
            text = colored('\n\n********************Stanford Pipelining of Sentences completed!********************\n\n', 'green', attrs = ['bold'])
            print (text)
            error_operations_obj.stanford_core_nlp_stage = 'Stanford corenlp xml output complete'
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Stanford Pipelining of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            print (text)    
            error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Stanford Pipelining of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)    
    os.chdir(base_dir)

def preprocess():

    if not os.path.exists(preprocess_dynamic_dir):
        os.makedirs(preprocess_dynamic_dir)
    #TODO:Observe and change
    os.chdir(preprocess_dir)
    try:
        try:
            # call(py_interp + [preprocess_script, '1', preprocess_dynamic_dir, ' '.join(py_interp)])
            preprocess_functions.preprocess_function('1', preprocess_dynamic_dir, error_operations_obj)
            #preprocess('1')
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Preprocessing of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            print (text)
            
        try:
            # call(py_interp + [preprocess_script, '2', preprocess_dynamic_dir, ' '.join(py_interp)])
            preprocess_functions.preprocess_function('2', preprocess_dynamic_dir, error_operations_obj)
            #prepro('2')
            text = colored('\n\n********************Preprocessing of Sentences completed!********************\n\n', 'green', attrs = ['bold'])
            print (text)
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Preprocessing of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            print (text)

        	

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Preprocessing of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
    os.chdir(base_dir)

def pyramid():
    os.chdir(pyramid_dir)
    try:
        #Wasih (02-21-21) Deep Clean (folders scu, sizes, pyrs/pyramids too)
        if not os.path.exists(os.path.join(scoring_dir, 'scu')):
            os.makedirs(os.path.join(scoring_dir, 'scu'))
        
        if not os.path.exists(os.path.join(scoring_dir, 'sizes')):
            os.makedirs(os.path.join(scoring_dir, 'sizes'))

        if not os.path.exists(os.path.join(scoring_dir, 'pyrs', 'pyramids')):
            os.makedirs(os.path.join(scoring_dir, 'pyrs', 'pyramids'))
        
        if not os.path.exists(os.path.join(scoring_dir,'temp')):
            os.makedirs(os.path.join(scoring_dir, 'temp'))

        if not os.path.exists(os.path.join(scoring_dir,'temp')):
            os.makedirs(os.path.join(scoring_dir, 'temp'))
        pyramidmain(pyramid_name)
        text = colored('\n\n********************Pyramid Building of Reference summaries completed!********************\n\n', 'green', attrs = ['bold'])
        print (text)	
    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Pyramid Building of Reference summaries threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
    os.chdir(base_dir)

def score():

    #Changes to process pyramid from MongoDB
    pyramid_operations_object = pyramid_operations_mongo_new.PyramidOperations(student_metadata_obj.essay_number, pyramid_dir, mongodb_operations)
    pyramid_operations_object.get_pyramid()

    error_operations_obj.pyramid_creation_stage = 'Creation of the pyramid xml/size files from the human-readable pyramid (if applicable) complete'

    #Changing the Pyramid Directory as per student
    essay_pyramid_dir = pyramid_operations_object.dynamic_pyr_dir

    #Passing config parser as an argument
    if not os.path.exists(scoring_dir):
        os.makedirs(scoring_dir)

    os.chdir(scoring_dir)
    try:
        scoring_functions.scoring_function(scoring_dynamic_dir, essay_pyramid_dir, output_filepath, log_dir, scoring_dir, config, error_operations_obj, mongodb_operations, student_metadata_obj)
        # call_s = py_interp + [scoring_script] + params
        # call(call_s)
        error_operations_obj.scoring_stage = 'Scoring Results complete'
        #Extract Intermmediate Files
        error_operations_obj.extract_file_data()
        #Push the error object to the db
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        text = colored('\n\n********************Scoring of summaries completed!********************\n\n', 'green', attrs = ['bold'])
        print("Score Complete")

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Scoring of summaries threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)

    os.chdir(base_dir)
    
    

def clean():
    try:
        shutil.rmtree(dynamic_base_dir, ignore_errors=True)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (e))
    
    #Wasih (02-21-20) Print colored text for user-friendliness
    text = colored('All temporary data deleted!', 'yellow')
    print (text)

def change_py_interp(params):
    global py_interp
    py_interp = params

def error_print(e1, e2=None):
    print('ERROR: ' + e1)
    if e2:
        print(e2)

if __name__ == "__main__":

    try:

        config = configparser.ConfigParser()
        config.read('parameters.ini')

        #TODO:Change to receive from notebook
        global student_metadata_obj
        #TYPES OF student_metadata(STRING, STRING, STRING, INT32, STRING) in DB
        student_metadata_obj = Student_Essay_Model.student_metadata("123", "1", "JK", 1, "O")

        # base_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = config.get('DynamicPaths', 'dynamicbasedir')
        pre_dynamic_base_dir = config.get('DynamicPaths', 'dynamicbasedir')
        static_base_dir = config.get('StaticPaths', 'staticbasedir')
        
        # student_list = []
        # documents = mongodb_operations.get_students(2)  

        #Changing the base dir in parameters to student's temporary folder
        #TODO: get this from parameters.ini
        dynamicbasedir = pre_dynamic_base_dir  + "/Student_" + str(student_metadata_obj.student_id)
        if not os.path.exists(dynamicbasedir):
                    os.makedirs(dynamicbasedir)
        
        config.set('DynamicPaths', 'dynamicbasedir', dynamicbasedir)

        #Student Changes end

        #Wasih (02-20-20) Make ConfigParser
        dynamic_base_dir = config.get('DynamicPaths', 'dynamicbasedir')
        raw_peer_dir = config.get('DynamicPaths', 'RawPeerDir')
        raw_model_dir = config.get('DynamicPaths', 'RawModelDir')
        split_peer_dir = config.get('DynamicPaths', 'SplitPeerDir')
        split_model_dir = config.get('DynamicPaths', 'SplitModelDir')
        preprocess_dir = config.get('DynamicPaths', 'PreprocessDynamicDir')
        preprocess_dynamic_dir = config.get('DynamicPaths', 'PreprocessDynamicDir')
        preprocess_peers_dir = config.get('DynamicPaths', 'PreprocessPeersDir')
        preprocess_model_dir = config.get('DynamicPaths', 'PreprocessModelDir')
        ext_dir = config.get('DynamicPaths', 'ExtDir')
        log_dir = config.get('DynamicPaths', 'LogDir')
        scoring_dynamic_dir = config.get('DynamicPaths', 'ScoringDynamicDir')
        output_filepath = config.get('DynamicPaths', 'OutputFile')
    
        seg_method = config.get('Segmentation', 'Method')

        py_interp = [config.get('StaticPaths', 'PythonInterp')]
        preprocess_script = config.get('StaticPaths', 'PreprocessScript')
        pyramid_dir = config.get('StaticPaths', 'PyramidDir')
        pyramid_script = config.get('StaticPaths', 'PyramidScript')
        scoring_dir = config.get('StaticPaths', 'ScoringStaticDir')
        scoring_script = config.get('StaticPaths', 'ScoringScript')
        pyramid_name = config.get('StaticPaths', 'OutputPyramidName')
        split_script = config.get('StaticPaths', 'SplitScript')
        stanford_dir = config.get('StaticPaths', 'StanfordDir')
        stanford_script = config.get('StaticPaths', 'StanfordScript')
        abcd_dir = config.get('StaticPaths', 'ABCDDir')
        preprocess_static_dir = config.get('StaticPaths', 'PreprocessStaticDir')

        error_operations_obj.set_dir(dynamic_base_dir)

    
        choice_dict = {
            'a': autorun,
            '1': splitsent,
            '2': stanford,
            '3': preprocess,
            '4': score,
            'i': change_py_interp,
            'q': quit,
        }    

        print(INSTRUCTIONS)
        while True:
            try:
                #Wasih (02-27-20) If python 2 => use raw_input, else use input
                if PYTHON_VERSION == 2:
                    user_in = raw_input(INPUT_STR)
                else:
                    user_in = input(INPUT_STR)
            except (EOFError, KeyboardInterrupt):
                sys.exit(0)
            if (len(user_in) == 0):
                continue
            tokens = user_in.split()
            command = tokens[0]
            try:
                choice = choice_dict[command]
            except KeyError:
                error_print('Bad command')
                continue
            choice()
            

    except Exception as e:
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        print('Error %s' %e)

    



