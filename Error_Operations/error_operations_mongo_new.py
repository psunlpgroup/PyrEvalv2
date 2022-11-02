# Written by: Adithya Tanam
# Last Update: 10/29/22

#Script to handle Error Operations

import os
class error_object:

    dynamic_base_dir = ''

    #File Content variables
    split_file_content = ''
    xml_file_content = ''
    segs_file_content = ''
    vector_file_content = ''
    temp_file_content = ''
    error_message = []

    #Messages 
    sent_split_stage = ''
    stanford_core_nlp_stage = ''
    seg_file_creation_stage = ''
    ls_file_creation_stage = ''
    pyramid_creation_stage = ''
    temp_segs_creation_stage = ''
    scoring_stage = ''

    def set_dir(self, dynamic_base_dir):
        self.dynamic_base_dir = dynamic_base_dir

    def extract_file_data(self):
        student_id = os.path.basename(self.dynamic_base_dir)
        split_file_path = os.path.join(self.dynamic_base_dir,'Raw/peers/split/', student_id)
        xml_file_path = os.path.join(self.dynamic_base_dir,'Preprocess/peer_summaries', (str(student_id) + ".xml"))
        segs_file_path = os.path.join(self.dynamic_base_dir,'Preprocess/peer_summaries/1', (str(student_id) + ".segs"))
        vector_file_path = os.path.join(self.dynamic_base_dir,'Preprocess/peer_summaries/1', (str(student_id) + ".ls"))
        temp_file_path = os.path.join(self.dynamic_base_dir,'temp/temp.segs')

        self.split_file_content = self.extract_data(split_file_path)
        self.xml_file_content = self.extract_data(xml_file_path)
        self.segs_file_content = self.extract_data(segs_file_path)
        self.vector_file_content = self.extract_data(vector_file_path)
        self.temp_file_content = self.extract_data(temp_file_path)

    def extract_data(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding = 'UTF-8') as f:
                return f.readlines()
        else:
            return 'file not generated'

    def add_message(self, stage_completed):
        self.error_message.append(stage_completed)

    def insert_data(self, student_object, mongodb_object):
        mongodb_object.insert_debug_data(student_object, self)

    

    
