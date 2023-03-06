# 	Script for cleaning the files and splitting the lines

#    Copyright (C) 2017 Yanjun Gao

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from nltk import sent_tokenize,word_tokenize
import re
import os
import glob 
import sys
#Wasih (02-25-20) Incorporate more things like abbreviations in sentence split
import ast

#Wasih (02-26-20) Make conditional imports depending on Python version
if sys.version_info[0] == 2:
        import ConfigParser as configparser
else:
        import configparser
        
#Wasih (02-19-20) Use functions instead of calling script
#inpath = sys.argv[1]
#outpath = sys.argv[2]

def stemming(text): 
	#dic = enchant.Dict("en_US")
	text = text.decode("utf-8","ignore")
	tokens = nltk.word_tokenize(text) 
	stems = []
	for item in tokens: 
		stems.append(en.lemma(item.lower()))
	data = " ".join(stems)
	#print "After stemming, take a look at the data---->\n: ",data
	#print "<--------"		
	return data 	#after return, the program won't go down

def removesymbols(text):
	tmp = []
	result = ''.join([i for i in text if not i.isdigit()])
	rmv0 = re.findall(r"[\w!,.:;']+",result)
	ele = ' '.join(rmv0)
	return ele

#Wasih (02-25-20) Incorporate normalization in sentence split
def normalize(content, config):
	'''
	Replace specific words in sentences (according to config file) by their normalized versions.
	Then return the final string
	'''
	abvs = config.get('Normalization', 'Abbs')
	#abvs has the structure of a dictionary with lists of values
	#use ast (abstract syntax tree) to parse it to a dictionary first
	abvs = ast.literal_eval(abvs)
	
# Modified code to fix issues with not getting all the files and trying to open split folder as file

#Wasih (02-19-20) Use functions instead of calling script
def split(inpath, outpath, mongodb_operations, student_metadata_obj):
	#Wasih (02-25-20) Read in normalization schemes and parse it	
	config = configparser.ConfigParser()
	config.read('parameters.ini')
	
	for filename in glob.glob(inpath + '/*'):

		#Getting the essay from the database
		content = mongodb_operations.get_student_essay(student_metadata_obj)
		#Becky 2/24eve next several lines in case content is null
		if content:
			content = removesymbols(content)

			sent_list = sent_tokenize(content)

			slash = filename.rfind('/')
			fn = outpath + "/Student_" + str(student_metadata_obj.student_id)
			with open(fn,'w') as wf:
				for i in sent_list:
					wf.write(i+'\n')
								
		# Old code for reference
		"""
		for filename in glob.glob(inpath + '/*'):
			content = open(filename).read()
			content = removesymbols(content)
			sent_list = sent_tokenize(content)
			slash = filename.rfind('/')
			fn = outpath+filename[slash:]
			with open(fn,'wb') as wf:
				for i in sent_list:
					wf.write(i+'\n')
		"""
