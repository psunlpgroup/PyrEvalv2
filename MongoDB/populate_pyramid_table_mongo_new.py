# Written by: Adithya Tanam
# Last Update: 10/29/22

# Script to populate hrp content to the pyramid collection from the HRP Folder

import mongo_db_functions
# START CHANGES RJP 3/03/23
import os
import sys
import mongo_db_functions

PYTHON_VERSION = 2
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser
    PYTHON_VERSION = 3

config = configparser.ConfigParser()
parametersfile = os.path.join(os.getcwd(),"parameters.ini")
config.read(parametersfile)
basedir = config.get('StaticPaths', 'staticbasedir')
# END CHANGES RJP 3/03/23
# START CHANGES MS 3/03/23
db_conn = config.get('Database', 'db_conn')
database_name = config.get('Database', 'database_name')
# END CHANGES MS 3/03/23

mongodb_operations = mongo_db_functions.MongoDB_Operations(db_conn)

if __name__ == "__main__":
    # RJP 03/03/23 replaced abs path with relative path
    hrp_location = os.path.join(basedir, "MongoDB/HRP_Files/essay1_pyramid_readable_20221207.pyr")
    # must cast the pyramid_id as float
    pyramid_id = float(20221207)             
    pyramid_name = "essay1_pyramid_readable_20221207"
    essay_number = 1
    essay_main_ideas = ["1", "2", "3", "4", "5", "6"]
    scu_mapping = ["5", "0", "4", "2", "1", "3"]

    # Code to connect to the databse
    mongodb_operations.connect(database_name);

    mongodb_operations.populate_pyramids(pyramid_id, pyramid_name, hrp_location)

    # Added 2/17/23 to ensure that the essay_main_ideas to scu_mapping and the essay number are populated in the db along with the pyramid that is read in
    mongodb_operations.populate_essay_pyramid(pyramid_id, essay_number, essay_main_ideas, scu_mapping)
