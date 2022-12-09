# Written by: Adithya Tanam
# Last Update: 10/29/22

# from MongoDB import mongo_db_functions
import configparser
import os
import xml.etree.ElementTree as gfg


class PyramidOperations:
    mongodb_operations = None
    pyramid_file_location = ''
    pyramid_id = None
    pyr_file_content = ''
    size_file_content = ''
    pyr_file_path = ''
    size_file_path = ''
    dynamic_pyr_dir = ''


    def __init__(self, essay_number, static_pyramid_dir, mongo_db_operations):
        self.mongodb_operations = mongo_db_operations

        config = configparser.ConfigParser()
        config.read('parameters.ini')

        self.pyramid_id = self.mongodb_operations.get_pyramid_id(essay_number)

        self.dynamic_pyr_dir = static_pyramid_dir + "/Pyramid_" + str(self.pyramid_id)

        if not os.path.exists(self.dynamic_pyr_dir):
            os.makedirs(self.dynamic_pyr_dir)

        self.pyr_file_path = self.dynamic_pyr_dir + "/Pyramid_" + str(self.pyramid_id) + '.pyr'
        self.size_file_path = self.dynamic_pyr_dir + "/Pyramid_" + str(self.pyramid_id) + '.size'

    def local_pyramid_check(self): 
        if (os.path.exists(self.pyr_file_path) and os.path.exists(self.size_file_path)):
            return True
        else:
            return False

    def get_pyramid(self):
        #get created pyramid from the database
        self.mongodb_operations.get_pyramid(self)


    def make_pyramid(self, hrp_content):
        # Program assumes that the Pyramid is made from 5 essays
        counts = [0 for i in range(5)]

        root = gfg.Element('Pyramid')

        scu_count = -1  

        for line in hrp_content:
            if line[:2] == '//':
                continue
            try:
                _, scuid, weight, text = line.split('\t')
            except:
                print(line)

            if scu_count != scuid:
                scu = gfg.Element('scu')
                scu.set('uid',scuid)
                root.append(scu)
                scu_count = scuid
                counts[int(weight)-1] +=1


            cont = gfg.SubElement(scu, "contributor")
            cont.set('label', text[:-1])


        tree = gfg.ElementTree(root)

        with open (self.pyr_file_path, "wb") as file :
                tree.write(file)

        with open (self.size_file_path, "w") as file:
            for i in counts:
                file.write(str(i)+'\n')

        with open(self.pyr_file_path, 'r', encoding = 'UTF-8') as f:
                self.pyr_file_content = f.readlines()

        with open(self.size_file_path, 'r', encoding = 'UTF-8') as f:
                self.size_file_content = f.readlines()

        self.mongodb_operations.update_pyramid(self.pyramid_id, self.pyr_file_content, self.size_file_content)
 
    def create_pyramid_files(self, pyr_file_content, size_file_content):
        pyr_file_content = str(pyr_file_content).strip('[').strip(']').strip('\'')
        size_file_content = str(size_file_content).strip('[').strip(']').strip('\'')

        with open(self.pyr_file_path, 'w') as pyr_file:
            pyr_file.write(pyr_file_content)

        #formating string representation to list
        size_file_content = size_file_content.strip('][').replace('\\n','').replace('\'','').replace(" ", '').split(',')
        
        with open(self.size_file_path, 'w') as size_file:
            for size in size_file_content:
                size_file.write(size + '\n')

        

        

