# Script for all functions used in scoring.py 

#    Copyright (C) 2017 Yanjun Gao

#    This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from sklearn.metrics.pairwise import cosine_similarity as cos
from printEsumLog import *
import pickle
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import copy
import statistics 
from bs4 import BeautifulSoup as Soup
import sys
import os
sys.path.append('../Preprocess/')
from weiwei import vectorize
from sif_embedding import vectorize_sif
import numpy as np 
import pandas as pd
import glob

#Wasih: 05-23-21 configurable scoring: read configurable parameters from config file
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser

config = configparser.ConfigParser()
config.read('../parameters.ini')

"""
===================== Segments =====================
"""

class Segment():
    def __init__(self, sentence_id, segment_id, segments = []):
        self.sentence_id = sentence_id
        self.segment_id = segment_id
        self.segments = segments
        self.length = len(segments)
        self.used = False
        self.text = {}
        self.scu_text_pairs = {}
    def addSegment(self, segment):
        self.segments += segment
    def setText(self, text):
        self.text = text
    def setSCUTextPairs(self, scu_text_pairs):
        self.scu_text_pairs = scu_text_pairs
#    def toString(self)
#        return str(self.sentence_id)+'\n'+str(self.segment_id)+'\n'+"\n".join(self.segments)+'\n'+str(self.length)+'\n'+

def parseMaxSegment(segment_list, number_of_sentences, used_sentence_list):
    candidates = [segment for segment in segment_list if segment.used == False]
    return_list = []
    for i in range(1, number_of_sentences + 1):
        if i not in used_sentence_list:
            max_c = 0
            for candidate in candidates:
                if candidate.sentence_id == i:
                    if candidate.length > max_c:
                        max_c = candidate
            if max_c != 0:
                max_c.used = True
                return_list.append(max_c)
    return return_list


"""
===================== SCU ======================
"""

def normalize(lst, typ):
    if typ == 'cosine':
        min_val = 0.5
        rang = 0.5
    else:
        min_val = 1
        rang = 4
    # rang = max(lst) - min_val
    return [(x-min_val)/rang for x in lst]

class SCU():
    def __init__(self, scu_id, weight, segment_embeddings):
        self.id = scu_id
        self.embeddings = segment_embeddings
        self.weight = weight
    def averageSimilarity(self, segment_embedding):
        normalizer = len(self.embeddings)
        # if normalizer == 0:
            # print (self.id) 
        # Puru 06/25/21 Added info to get std dev of cosine similarity of SCUs contributors with the segment
        similarities = []
        segment_embedding = np.array([segment_embedding])
        segment_embedding.reshape(-1,1)
        for embedding in self.embeddings:
            # By Yanjun: For testing 
            embedding = np.array([embedding])
            #print "embedding", embedding
            
            #print "embedding", segment_embedding
            embedding.reshape(-1,1)
            #Wasih: 05-23-21 configurable scoring: Read the distance measure from config file to compute distance between embedding vectors, for eg. cos
            distance_method = config.get('Scoring_Params', 'DistanceMethod')
            if distance_method == 'cos':
                similarities.append(cos(embedding, segment_embedding)[0][0])
            similarity = sum(similarities)
            stddev = np.std(similarities)
            #similarity += cos(embedding, segment_embedding)[0][0]
            #similarity += cos(embedding, segment_embedding)
            # For testing purpose, change simiarity threshold to 4.0  
        #if similarity / normalizer < 4.35146819363:
        #Wasih: 05-23-21 configurable scoring: Read threshold from config fil
        edge_threshold = float(config.get('Scoring_Params', 'EdgeThreshold'))
        if similarity / normalizer < edge_threshold:
            return None
        else:
            return [similarity / normalizer, self.weight, stddev]

"""
============== Sentence Graph ====================
"""
def weight_fn(cosine, weight):
    fn = cosine * weight
    return fn

class SentenceGraph():
    """ Given a Sentence, build a graph from segmentations """
    def __init__(self, sentence_id, segmentations, scus):
        self.sentence_id = sentence_id
        self.segmentations = segmentations
        self.graph = self.buildGraph(scus)
    def buildGraph(self, scus):
        segmentations = self.segmentations
        graph = []
        for segmentation, segments in segmentations.items():
            hypernode = []
            for segment_id, segment_embedding in segments.items():
                scu_list = self.findSCUs(segment_embedding, scus)
                hypernode.append(Vertex(segment_id, scu_list))
            graph.append(hypernode)
        return graph
    def findSCUs(self, segment_embedding, scus):
        scores = {}
        for scu in scus:
            average = scu.averageSimilarity(segment_embedding)
            if average != None:
                scores[scu.id] = average
        #Wasih: 05-23-21 configurable scoring: top k scus to consider for making the most similar scus matching the given segment embedding
        top_k_scus = int(config.get('Scoring_Params', 'TopKScus'))
        sort_fn = config.get('Scoring_Params', 'SortingMetric')

        cos = normalize([x[1][0] for x in scores.items()], 'cosine')
        wts = normalize([x[1][1] for x in scores.items()], 'weight')
        std = [1-x[1][2] for x in scores.items()]
        wtdsum = []
        for i in range(len(scores.items())):
            wtdsum.append((cos[i], wts[i], std[i]))
        # wtdsum = [(x,y,z) for x in cos for y in wts for ]
        # print (wtdsum)
        for i, each in enumerate(scores.items()):
            each[1].append(wtdsum[i])
        if sort_fn == "product":
            scores = sorted(scores.items(), key=lambda x:x[1][0]*x[1][1], reverse=True)[:top_k_scus]
            #scores = [(score[0], score[1][0], score[1][1], score[1][2]) for score in scores]
        elif sort_fn == "stddev":
            scores = sorted(scores.items(), key=lambda x:x[1][0]*x[1][1]*(1-x[1][2]), reverse=True)[:top_k_scus]
            #scores = [(score[0], score[1][0], score[1][1], score[1][2]) for score in scores]
        elif sort_fn == "cosine":
            scores = sorted(scores.items(), key=lambda x:x[1][0], reverse=True)[:top_k_scus]
            #scores = [(score[0], score[1][0], score[1][1], score[1][2]) for score in scores]
        elif sort_fn == "normsum":
            scores = sorted(scores.items(), key=lambda x:x[1][3][1]+x[1][3][0]+x[1][3][2], reverse=True)[:top_k_scus]
                # print(scores)
                #scores = [(score[0], score[1][0], score[1][1], score[1][2], score[1][3]) for score in scores]
        elif  sort_fn == "wtdsum":
            weights = (1,0,1)
            scores = sorted(scores.items(), key=lambda x:x[1][3][1]*weights[1]+x[1][3][0]*weights[0]+x[1][3][2]*weights[2], reverse=True)[:top_k_scus]

        #scores = [(score[0], score[1][0]) for score in scores]
        #Wasih (06-14-21) Add another element (SCU weight) to make the scores/scu list as that of triples
        #Puru 06/25/21 Added 4th element (SCU standard deviation) to make a 4 tuple for each SCU
        scores = [(score[0], score[1][0], score[1][1], score[1][2], score[1][3]) for score in scores]
        return scores
        

class Vertex():
    def __init__(self, segment_id, scu_list):
        self.id = segment_id
        self.scu_list = scu_list
        self.neighbors = []
        self.useMe = True
        self.max = False
        self.used = True
    def getWeight(self):
        #Wasih: 05-23-21 configurable scoring: vertex weighting scheme
        weight_scheme = config.get('Scoring_Params', 'WeightScheme')
        #Puru 06/25/21 Fixed the bug and added functionality to change the function
        weight_fn = config.get('Scoring_Params', 'WeightingMetric')
        
        weights = []
        # print(self.scu_list)
        if weight_fn == "product":
            weights = [scu[1]*scu[2] for scu in self.scu_list]
        elif weight_fn == "stddev":
            weights = [scu[1]*scu[2]*(1-scu[3]) for scu in self.scu_list]
        elif weight_fn == "cosine":
            weights = [scu[1] for scu in self.scu_list]
        elif weight_fn == "wtdsum" or weight_fn == "normsum":
            #print(list(self.scu_list))
            if weight_fn == "wtdsum":
                wts = (1,0,1)
            else:
                wts = (1,1,1)
            weights = [scu[4][0]*wts[0] + scu[4][1]*wts[1] + scu[4][2]*wts[2] for scu in self.scu_list]
        
        
        
        if weight_scheme == 'average':
            if len(self.scu_list) != 0:
                return sum(weights)/ len(self.scu_list)
            else:
                return 0
        elif weight_scheme == 'sum':
            #Wasih: 05-23-21 Possible bug: Correct it to scu[1] (this is cosine similarity), as scu[0] is just the scu id

            if len(self.scu_list) != 0:
                return sum(weights)
            else:
                return 0
        elif weight_scheme == 'max':
            if len(self.scu_list) != 0:
                return max(weights)
            else:
                return 0


        ###### Weight Scheme 1
        #return sum([scu[1] for scu in self.scu_list]) / len(self.scu_list)
        ###### Weight Scheme 2
        #Wasih: 05-23-21 Possible bug: Correct it to scu[1] (this is cosine similarity), as scu[0] is just the scu id
        #return sum([scu[1] for scu in self.scu_list])
        ###### Weight Scheme 3
        #return max([scu[1] for scu in self.scu_list])

    def getValues(self):
        return self.scu_list       
    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)
        neighbor.we_are_neighbors(self)
    def add_neighbors(self, *args):
        for neighbor in args:
            self.neighbors.append(neighbor)
            neighbor.we_are_neighbors(self)
    def we_are_neighbors(self, neighbor):
        self.neighbors.append(neighbor)
    def delete(self):
        self.useMe = False
        for neighbor in self.neighbors:
            neighbor.useMe = False

class SummaryGraph():
    def __init__(self, sentences, scus):
        self.sentences = [SentenceGraph(n, segmentations, scus) for n, segmentations in sentences.items()]
        for sentence in self.sentences:
            self.buildInnerEdgesList(sentence.graph)
        self.vertices = self.buildOuterEdgesList()
        self.independentSet, self.independentSetValues = self.buildIndependentSet()
    def buildInnerEdgesList(self, sentenceGraph):
        nodes = list(sentenceGraph)
        while len(nodes) > 0:
            node = nodes[0]
            for vertex in node:
                for n in nodes[1:]:
                    for vert in n:
                        vertex.add_neighbor(vert)
            nodes = nodes[1:]
    def buildOuterEdgesList(self):
        sentences = list(self.sentences)
        vertex_list = []
        while (len(sentences) > 0):
            sentence = sentences[0]
            for node in sentence.graph:
                for vertex in node:
                    vertex_list.append(vertex)
                    for sent in sentences[1:]:
                        for n in sent.graph:
                            for vert in n:
                                if set(vertex.scu_list) & set(vert.scu_list):
                                    vertex.add_neighbor(vert)
            sentences.remove(sentence)
        return vertex_list
    def buildIndependentSet(self):
        vertices = copy.deepcopy([vertex for vertex in self.vertices if vertex.useMe == True])
        independentSet = []
        while len(vertices) != 0:
            vertex = max(vertices, key=lambda x: x.getWeight())
            independentSet.append(vertex)
            vertex.delete()
            vertices = [vert for vert in vertices if vert.useMe == True]
        for each in independentSet:
            values = [(each.id, each.getValues()) for each in independentSet]
            # print(each.id, each.getValues())
        return independentSet, values


"""
============= Reading Human Pyramids ============
"""

def getSoup(fname):
    # print(fname)
    handler = open(fname, 'r')
    soup = Soup(handler, 'lxml')
    return soup
def getSCUs(soup):
    scus = {}
    for scu in soup.find_all('scu'):
        labels = []
        scu_id = scu.get('uid')
        children = scu.find_all('contributor')
        for child in children:
            labels.append(child.get('label'))
        scus[int(scu_id)] = labels
    return scus 
def vecotirizationProtocol(fname):
    cwd = os.getcwd()
    os.chdir('../Preprocess/')
    fname = '../Scoring/' + fname
    #By Yanjun : weiwei's method
    vec_method = config.get('Vectorization', 'Method')
    #Puru (07-17-21): Need to add glove vectorization while vectorizing scu segments too
    if vec_method == 'wtmf':
        vecs = vectorize(fname)
    elif vec_method == 'glove':
        vecs = vectorize_sif(fname)
    #By Yanjun: SIF method 
    #vecs = vectorize_sif(fname)
    os.chdir(cwd)
    return vecs
def vectorizeSCUs(scus):
    reconstruction = {}
    scs = {}
    document = []
    scu_ids = []
    scus = sorted(scus.items(), key=lambda x: len(x[1]), reverse=True)
    for scu_id, contributor in scus:
        scu_ids.append((scu_id, len(contributor)))
        scs[scu_id] = contributor
        document += contributor
    fname = 'temp/tmp.segs'
    with open(fname, 'w') as f:
        for line in document:
            f.write(line + '\n')
    f.close()
    vecs = vecotirizationProtocol(fname)
    j = 0
    for scu_id, length in scu_ids:
        reconstruction[scu_id] = vecs[j:length]
        vecs = vecs[length:]
    return reconstruction, scs
def readPyramid(fname):
    soup = getSoup(fname)
    scus = getSCUs(soup)
    recon, scus = vectorizeSCUs(scus)
    #print "recon, ", recon
    scu_objects = []
    layer_sizes = []
    for scu_id, labels in recon.items():
        #print "scu id ", scu_id
        #print "labels ", labels 
        scu_objects.append(SCU(scu_id, len(labels), labels))
    size = max(scu_objects, key=lambda x: x.weight).weight
    j = 0
    for scu in scu_objects:
        if scu.weight < size:
            layer_sizes.append(j)
            j = 1
            size = scu.weight
        else:
            j += 1
    else:
        layer_sizes.append(j)
    fname = 'sizes/' + filename(fname) + '.size'
    with open(fname, 'w') as f:
        for size in layer_sizes:
            f.write(str(size) + '\n')
    f.close()
    return scu_objects, scus


"""
============= Function Definitions ===============
"""

def buildSCUlist(scu_pickle):
    with open(scu_pickle, 'rb') as f:
        SCUs = pickle.load(f)
    f.close()
    scus =[]
    for scu_id, weight_embeddings in SCUs.items():
        scus.append(SCU(scu_id, int(weight_embeddings[0]), weight_embeddings[1]))
    return scus

def sentencesFromSegmentations(fname):
    f = open(fname, 'r') # Read in file
    segments = f.readlines() # Each line is a segment
    sentences = {} # Initialize Empty Directory
    for segment in segments:
        segment = segment.split('&')
        if segment[1] in sentences.keys(): # segment[1] is the sentence identitiy
            embedding = segment[4].strip('\n').replace('[', '').replace(']', '') # rip out the embedding from the line
            embedding = [float(i) for i in embedding.split(',')] # cast elements to float with list comprehension
            sentences[segment[1]].append({'&'.join(segment[:4]):embedding}) # segment id: embedding
        else:
            embedding = segment[4].strip('\n').replace('[', '').replace(']', '')
            embedding = [float(i) for i in embedding.split(',')]
            sentences[segment[1]] = [{'&'.join(segment[:4]):embedding}]
    sentences = sorted(sentences.items(), key=lambda x: int(x[0])) # nested dictionary (sentence_key, sentence_stuff)
    sentences = [sentence[1] for sentence in sentences]
    sents = []
    segmentations_in_summary = 0
    seg_ids = []
    for n, sentence in enumerate(sentences):
        segmentations = {}
        count = {}
        for segment in sentence:
            for segment_id, embedding in segment.items():
                seg_ids += [segment_id]
                if segment_id.split('&')[2] in segmentations.keys():
                    segmentations[segment_id.split('&')[2]][segment_id] = embedding
                    count[segment_id.split('&')[2]] += 1
                else:
                    segmentations[segment_id.split('&')[2]] = {}
                    segmentations[segment_id.split('&')[2]][segment_id] = embedding
                    count[segment_id.split('&')[2]] = 1
        sents.append(segmentations)
        segmentations_in_summary += max(count.items(), key=lambda x: x[1])[1]
    segment_list = sortSegmentations(dict(enumerate(sents)))
    return dict(enumerate(sents)), segmentations_in_summary, segment_list

def sortSegmentations(segmentation_dict):
    segment_list = []
    for sentence, segmentations in segmentation_dict.items():
        sentence_id = int(sentence) + 1
        #print sentence_id
        for segment_id, segmentation_list in segmentations.items():
            for segment_id, segmentation in segmentation_list.items():
                segment_id = int(segment_id.split('&')[2])

                segment_list += [Segment(sentence_id,segment_id, segmentation)]
    return segment_list

def buildSCUcandidateList(vertices):
    scu_and_segments = {}
    vertices = sorted(vertices, key = lambda x: int(x.id.split('&')[1]))
    for vertex in vertices:
        for scu in vertex.scu_list:
            if scu[0] in scu_and_segments.keys():
                scu_and_segments[scu[0]][vertex.id] = scu[1]
            else:
                scu_and_segments[scu[0]] = {}
                scu_and_segments[scu[0]][vertex.id] = scu[1]
    return scu_and_segments

def processResults(scu_and_segments, independentSet):
    scu_and_segments = copy.deepcopy(scu_and_segments)
    chosen = []
    chosen_scus = []
    segment_and_scu = {}
    segment_ids = []
    for scu, segments in scu_and_segments.items():
        segment_ids += segments
        for segment in list(segments):
            if segment in chosen:
                del segments[segment] 
        if len(segments) != 0:
            median = statistics.median_high(segments.values())
        for segment in list(segments):
            value = segments[segment]
            if value == median:
                segment_and_scu[segment] = scu
                #print(segment, scu)
                chosen.append(segment)
                chosen_scus.append(scu)
                del segments[segment]
    segment_ids = list(set(segment_ids))
    return segment_and_scu, len(segment_ids)

def scusBySentences(segment_scu):
    sentences = {}
    for segment, scu in segment_scu.items():
        sentence_id = segment.split('&')[1]
        if sentence_id in list(sentences):
            sentences[sentence_id][segment] = scu
        else:
            sentences[sentence_id] = {}
            sentences[sentence_id][segment] = scu
    return sentences

def getScore(sentences, scus):
    sentence_scores = {}
    matched_cus = 0
    for sentence in list(sentences):
        segments = sentences[sentence]
        lil_score = 0
        for segment, scu in segments.items():
            for s in scus:
                if scu == s.id:
                    #print s.weight
                    lil_score += s.weight
                    matched_cus += 1
        sentence_scores[sentence] = lil_score
    return sum(sentence_scores.values()), matched_cus

def filename(fname):
    slash = fname.rfind('/') + 1
    dot = fname.rfind('.')
    return fname[slash:dot]


'''
================== Scores and Results ================
'''
# Puru 02/18/22 Find group matchings for the notebook feedback
def getGroups(cu_vector):
    # Convert the groups to a file at some point once a standard format for the file can be decided
    groups = {'A' : [0], 'B' : [1], 'C' : [2], 'D' : [3]}
    results = [0]*len(groups)
    for i, each in enumerate(groups.keys()):
        vals = groups[each]
        match = 1
        for index in vals:
            match *= cu_vector[index]
        results[i] = match
    return results


#Puru (11-03-21) Added this function to move things from the main file to the helper library for better threading 

def score(scus, fn, raw_scores, quality_scores, coverage_scores, comprehension_scores, pyramid, pyramid_name, scu_labels, numsmodel, print_all, log, rf, cu_matches, group_matches):
    # if os.path.isdir(summary):
    #     summ = glob.iglob(summary+'/*')
    #     #fn is the summary name 
    #     for fn in summ:
    #         print ("current filename: ", fn)
    #         if fn.endswith('.ls'):
            # scus = copy.deepcopy(scus_og)
    summary_slash= fn.rfind('/') + 1
    summary_dot = fn.rfind('.')
    summary_name = fn[summary_slash:summary_dot]
    if os.path.getsize(fn) == 0:
        raw_scores[summary_name] = 0
        quality_scores[summary_name] = 0
        coverage_scores[summary_name] = 0
        comprehension_scores[summary_name] = 0
        return
    segs = fn[:fn.rfind('/')] + '/' + summary_name + '.segs'
    segs = open(segs, 'r').readlines()
    num_sentences = int(segs[len(segs)-1].split('&')[1])
    segs = {'&'.join(seg.split('&')[:4]): seg.split('&')[4] for seg in segs}
    sentences, segment_count, segment_list = sentencesFromSegmentations(fn)
    Graph = SummaryGraph(sentences, scus)
    independentSet = Graph.independentSet
    independentSetValues = Graph.independentSetValues
    candidates = buildSCUcandidateList(independentSet)
    #print "Candidates: ", 
    results, possiblyUsed = processResults(candidates, independentSet)
    segcount = getsegsCount(segment_list, results, segs, num_sentences)
    #print "Possibly used: ", possiblyUsed
    keys = [res.split('&') for res in results]
    rearranged_results = scusBySentences(results)
    score, matched_cus = getScore(rearranged_results, scus)
    size_file = 'sizes/' + filename(pyramid) + '.size'
    #count_by_weight, avg = getLayerSizes(size_file)
    # New get layersize 
    count_by_weight, avg = new_getlayersize(size_file,numsmodel)
    #print "AVG SCU: ", avg 
    raw_scores[summary_name] = score
    # temporary fix to number of sentences 
    #q_max = maxRawScore(count_by_weight, possiblyUsed)
    q_max = maxRawScore(count_by_weight, segcount)
    #print "MAXSUM for numbers of matched SCU", q_max 
    c_max = maxRawScore(count_by_weight, avg)

    #print "MAXSUM for avg scu: ", c_max 
    #print "score divided by max obtainable scores: ", q_max
    quality = 0 if not q_max else float(score)/q_max
    if quality > 1:
        quality = 1 
    coverage = 0 if not c_max else float(score)/c_max
    if coverage > 1:
        coverage = 1 
    comprehension = float((quality + coverage)) / 2
    quality_scores[summary_name] = quality
    coverage_scores[summary_name] = coverage
    comprehension_scores[summary_name] = comprehension

    # Puru 02/18/22 Additional code for the notebook input files
    cu_vector = [0]*15
    for each in results:
        if results[each] < 15:
            cu_vector[results[each]] = 1

    cu_matches[summary_name] = cu_vector
    group_vector = getGroups(cu_vector)
    group_matches[summary_name] = group_vector


    if (print_all) or log:
        #log_f = log + summary_name
        log_f = "../log/" + summary_name
        # loginput = open(log_f, "w+")
        # loginput = open("../log/loginput.txt", "w+")
        # loginput.write(summary_name+'\n'+str(segcount)+'\n'+str(score)+'\n'+str(quality)+'\n'+str(coverage)+'\n'+str(comprehension)+'\n'+str(results)+'\n'+" ".join(str(segment_list))+'\n'+str(num_sentences)+'\n'+str(segs)+'\n'+str(scu_labels)+'\n'+pyramid_name+'\n'+log_f)
        # loginput.close()
        # if not print_all:
        #     print("Success!!")
        printEsumLogWrapper(summary_name, segcount, score, quality, coverage, comprehension, q_max, c_max, avg, results, segment_list, num_sentences, segs, scu_labels, pyramid_name, log_f, independentSetValues, print_all)
       
    if rf:
        scores = [raw_scores, quality_scores, coverage_scores, comprehension_scores] 
        s = Summary(summary_name, segcount, segment_list, num_sentences, segs)
        p = Pyramid(scu_labels, pyramid_name)
        segList, SCUL = listSegments(s, p, results)
        dicti = getDictionary(segList, p, results, scores)
        #now write the dictionary to a pickle file which will then be read by the flask app
        dict_filename, _ = os.path.split(results_file)
        dict_filename = os.path.join(dict_filename, 'dict')
        f = open(dict_filename, 'wb')
        pickle.dump(dicti, f)
        #f.write(dicti)
        print(dicti)
        print('******************************\n\n')

def recall(results, fname):
    path = 'pan/op_' + filename(fname) + 'pan'
    orig_scus = []
    with open(path, 'r') as f:
        for line in f:
            line.split('\t')
            if type(line[0]) == int:
                if line[0] not in orig_scus:
                    orig_scus.append(line[0])

def maxRawScore(count_by_weight, num):
    counts = sorted(count_by_weight.items(), key=lambda x:x[0], reverse=True)
    result = 0
    for count in counts:
        if num >= count[1]:
            num = num - count[1]
            result = result + (count[0]*count[1])
        else:
            result = result + (num*count[0])
            num = 0
    return result

def new_getlayersize(sizefile, numsmodel):
    lines = open(sizefile).readlines()
    count = 0 
    count_by_weight = {}
    for ind in range(len(lines),0,-1):
        nums = int(lines[len(lines)-ind].strip()) * ind 
        # print ("layer: ", ind, " nums of SCU: ", int(lines[len(lines)-ind].strip()))
        count_by_weight[ind] = int(lines[len(lines)-ind].strip()) 
        count += nums 
    avg = count / numsmodel
    return count_by_weight, avg 

def getLayerSizes(fname):
    f = open(fname, 'r')
    lines = f.readlines()
    count_by_weight = {}
    count = 0
    for n, line in enumerate(lines):
        count_by_weight[n + 1] = int(line.strip())
        count += (n+1) * int(line.strip())
    avg = count/(n+1)
    return count_by_weight, avg

def retrieveSeg(segID, seg_list):
    for seg_id, seg in seg_list.items():
        if segID == seg_id:
            return seg

# Puru defunct function (refer to printEsumLog.py)
def formatVerboseOutput(summary_name,segment_count,score,quality,coverage,comprehension, results, segment_list,num_sentences,segs,scu_labels, pyramid_name, log_file):
    w,h = terminal_size()
    summary_name_len = len(summary_name)
    
    used_sentence_list = []
    check_tups = {}
    
    for s in segment_list:
        for res, scu in results.items():
            r = res.split('&')
            sentence_id = int(r[1])
            segment_id = int(r[2])
            segtation_id = int(r[3])
        
            if s.sentence_id == sentence_id:
                if s.segment_id == segment_id:
                    check_tup = (s.sentence_id, s.segment_id)
                    if check_tup in check_tups.keys():

                        if segtation_id not in check_tups[check_tup]:
                            check_tups[check_tup].append(segtation_id)
                            s.scu_text_pairs[int(r[3])] = scu
                            if sentence_id not in used_sentence_list:
                                used_sentence_list.append(sentence_id)
                    else:
                        check_tups[check_tup] = [segtation_id]
                        s.used = True
                        s.scu_text_pairs[int(r[3])] = scu
                        if sentence_id not in used_sentence_list:
                                used_sentence_list.append(sentence_id)


    for s in [s for s in segment_list if s.used == True]:
        for segment_id, segment in segs.items():
            sentence_id = int(segment_id.split('&')[1])
            segmentation_id = int(segment_id.split('&')[3])
            segment_id = int(segment_id.split('&')[2])
            if sentence_id == s.sentence_id:
                if segment_id == s.segment_id:
                    s.text[segmentation_id] = segment

    non_used_segments = parseMaxSegment(segment_list, num_sentences, used_sentence_list)
    for s in non_used_segments:
        for segment_id, segment in segs.items():
            sentence_id = int(segment_id.split('&')[1])
            segmentation_id = int(segment_id.split('&')[3])
            segment_id = int(segment_id.split('&')[2])
            if sentence_id == s.sentence_id:
                if segment_id == s.segment_id:
                    s.text[segmentation_id] = segment
    
    newSegmentList = [s for s in segment_list if s.used == True]

    cu_list = []
    for s in newSegmentList:
        for seg_index, text in s.text.items():
            if seg_index in s.scu_text_pairs.keys():
                cu = (s.scu_text_pairs[seg_index], len(scu_labels[s.scu_text_pairs[seg_index]]))
                cu_list.append(cu)
    if len(cu_list) != 0:
        cu_list = sorted(cu_list, key=lambda x:x[0], reverse=True)
        sorted_cu_list = {5:[], 4:[], 3:[], 2:[], 1:[]}
        for item in cu_list:
            sorted_cu_list[item[1]].append(item)
        cu_list = []
        for i in range(5, 0, -1):
            sorted_cu_list[i] = sorted(sorted_cu_list[i], key=lambda x:int(x[0]))
            cu_list.append(sorted_cu_list[i])
        
        print(cu_list)
        x = input()
        cu_line = ''
        
        for cu in cu_list[:len(cu_list)-1]:
            cu_line += str(cu[0]) + ': ' + str(cu[1]) + ', '
        cu_line += str(cu_list[len(cu_list)-1][0]) + ': ' + str(cu_list[len(cu_list)-1][1])
    else:
        cu_line = 'No Content Units'

    
    handler = open(log_file, 'w') if log_file else None

    print ('\n' + '#'*(w/2 - summary_name_len + 2) + '  ' + summary_name + '  ' + '#'*(w/2 - summary_name_len + 2) + '\n')
    handler.write('\n' + '#'*(w/2 - summary_name_len + 2) + '  ' + summary_name + '  ' + '#'*(w/2 - summary_name_len + 2) + '\n') if handler else None
    print ('Pyramid: %s' % pyramid_name)
    handler.write('Pyramid: %s\n' % pyramid_name) if handler else None
    
    print ('No. Segments in Summary: {}'.format(segment_count))
    handler.write('No. Segments in Summary: {}\n'.format(segment_count)) if handler else None

    print ('{:>17}: {:>10}\n{:>17}: {:>10.3f}\n{:>17}: {:>10.3f}\n{:>17}: {:>10.3f}'.format('Raw', score, 'Quality', quality, 'Coverage', coverage, 'Comprehensive', comprehension))
    handler.write('{:>17}: {:>10}\n{:>17}: {:>10.3f}\n{:>17}: {:>10.3f}\n{:>17}: {:>10.3f}\n'.format('Raw', score, 'Quality', quality, 'Coverage', coverage, 'Comprehensive', comprehension)) if handler else None

    print ('{:>17}: \t{}\n'.format('Content Unit List', cu_line))
    handler.write( '{:>17}: \t{}\n'.format('Content Unit List', cu_line)) if handler else None



    for s in newSegmentList:
        print ("Sentence: %d, Segmentation %d" % (s.sentence_id, s.segment_id))
        handler.write( "\nSentence: %d, Segmentation %d\n" % (s.sentence_id, s.segment_id)) if handler else None


        for seg_index, text in s.text.items():
            if seg_index in s.scu_text_pairs.keys():
                print ("\tSegment: %d | Content Unit: %d [Weight: %d]" % (seg_index, s.scu_text_pairs[seg_index], len(scu_labels[s.scu_text_pairs[seg_index]]))) 

                handler.write("\n\tSegment: %d | Content Unit: %d [Weight: %d]" % (seg_index, s.scu_text_pairs[seg_index], len(scu_labels[s.scu_text_pairs[seg_index]]))) if handler else None
                #handler.write("\n\t")
                print(wrap_string(s.text[seg_index].strip(), '\tSegment: ................. '))
                #handler.write(wrap_string(s.text[seg_index].strip(), '\n\tSegment: ................. ')) if handler else None
                handler.write("\n\tSegment: ................. "+s.text[seg_index].strip())

                content_unit = scu_labels[s.scu_text_pairs[seg_index]]
                for n, cu_part in enumerate(content_unit):
                    if n == 0:
                        print (wrap_string(cu_part, '\tContent Unit: ............ (%d) ' % (n+1)))
                        #handler.write(wrap_string(cu_part, '\n\tContent Unit: ............ (%d) \n' % (n+1))) if handler else None
                        handler.write('\n\tContent Unit: ............ (%d)' % (n+1)+ " "+cu_part+"\n")

                    else:
                        print (wrap_string(cu_part, "\t" + " "*13 + " ............ (%d) "  % (n+1)))                            
                        #handler.write(wrap_string(cu_part, "\n\t" + " "*13 + " ............ (%d) "  % (n+1))) if handler else None 
                        handler.write("\n\t" + " "*13 + " ............ (%d) "  % (n+1)+ " "+cu_part)
            else:
                print ("\tSegment: %d | Content Unit: None" % seg_index) 
                handler.write("\n\tSegment: %d | Content Unit: None\n" % seg_index) if handler else None

                print(wrap_string(s.text[seg_index].strip(), '\tSegment: ................. '))
                handler.write(wrap_string(s.text[seg_index].strip(), '\n\tSegment: ................. \n')) if handler else None

        print ("\n")
    print ("\n")
    handler.write("\n\n") if handler else None
    print ("="*w)
    handler.write("="*w) if handler else None
    print ("\n")
    handler.write("\n") if handler else None

    handler.close() 

"""
======= etc ==========
"""

def terminal_size():
    import fcntl, termios, struct
    h, w, hp, wp = struct.unpack('HHHH',
        fcntl.ioctl(0, termios.TIOCGWINSZ,
        struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h

def wrap_string(text, starter_text):
    # text is the part of the string that your want to wrap
    # started_text could also be a point about which the text wraps
    w,h = terminal_size()
    text = text.replace('\n', '')
    tabs = starter_text.count('\t')
    new_starter_text = starter_text.replace('\t', '')
    wrap_point = len(new_starter_text) + 8*tabs
    wrap_indicator = int(w) - wrap_point
    num_line_wraps = len(text) / wrap_indicator
    left_over = len(text) % wrap_indicator
    for i in range(num_line_wraps):
        lines.append(text[i:((i+1)*wrap_indicator)] + '\n')
    lines.append(text[-left_over:])
    lines = [starter_text + lines[0]] + [" "*wrap_point + line for line in lines[1:]]
    return ''.join(lines)

# Returns the number of segments in the list of matched and non matched segments used by the pyramid
def getsegsCount(segment_list, results, segs, num_sentences):
    checker = {}
    usedcounter = 0
    used_sentences = []
    for seg in segment_list:
        for res, scu in results.items():
            sentence_id, segmentation_id, segment_id = getMetadata(res)
            if segIsEqual(seg, sentence_id, segmentation_id):
                tup = (sentence_id, segmentation_id)
                if tup in checker.keys():
                    if segment_id not in checker[tup]:
                        checker[tup].append(segment_id)
                        usedcounter += 1
                else:
                    checker[tup] = [segment_id]
                    usedcounter +=1
                seg.scu_text_pairs[segment_id] = scu
                
                if sentence_id not in used_sentences:
                    used_sentences.append(sentence_id)
    
    used = {}
    counter = 0
    for s in segment_list:
        if s.sentence_id not in used_sentences:
            if (s.sentence_id,s.segment_id) not in used.keys():
                used[(s.sentence_id,s.segment_id)] = 1
            else:
                used[(s.sentence_id,s.segment_id)] = used[(s.sentence_id,s.segment_id)] + 1
        else:
            if (s.sentence_id, s.segment_id) in checker.keys():
                if (s.sentence_id,s.segment_id) not in used.keys():
                    used[(s.sentence_id,s.segment_id)] = 1
                else:
                    used[(s.sentence_id,s.segment_id)] = used[(s.sentence_id,s.segment_id)] + 1
                
    for i in range(1, num_sentences + 1):
        maxcount = 0
        for each in used.keys():
            if i == each[0]:
                if maxcount < used[each]:
                    maxcount = used[each]
        counter += maxcount
        
    # for each in used.keys():
        # print ("segment" + str(each)+ " : "+ str(used[each]))
    
    # print ("Total segments : "+str(counter))
    return counter

# Returns true if the segment has the same sentence id and segment id as the args
def segIsEqual(seg, sentence_id, segmentation_id):
    if seg.sentence_id == sentence_id and seg.segment_id == segmentation_id:
        return True
    else:
        return False

# Returns the sentence id, segment id, and segmentation id for the given arg line
def getMetadata(x):
    r = x.split('&')
    sentence_id = int(r[1])
    segmentation_id = int(r[2])
    segment_id = int(r[3])
    return sentence_id, segmentation_id, segment_id
