# Written by: Adithya Tanam
# Last Update: 10/29/22

# Script to populate hrp content to the pyramid collection from the HRP Folder

import mongo_db_functions
# START CHANGES RJP 3/03/23
import os
import sys
import mongo_db_functions
import argparse

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
# END CHANGES MS 4/05/23

mongodb_operations = mongo_db_functions.MongoDB_Operations(db_conn)

# Becky 4/7/23 added another attribute for this function to return: main_idea_accuracy
def populate_pyramid1():
    hrp_location = os.path.join(basedir, "MongoDB/HRP_Files/essay1_pyramid_readable_20221207.pyr")
    # must cast the pyramid_id as float
    pyramid_id = float(20221207)
    pyramid_name = "essay1_pyramid_readable_20221207"
    essay_number = 1
    essay_main_ideas = ["1", "2", "3", "4", "5", "6"]
    scu_mapping = ["5", "0", "4", "2", "1", "3"]
    main_idea_accuracy = {
                    "high_acc": ["2", "4", "6"],
                    "med_acc": ["1", "5"],
                    "low_acc": ["3"]
                    }

    return hrp_location, pyramid_id, pyramid_name, essay_number, essay_main_ideas, scu_mapping, main_idea_accuracy

# Becky 4/7/23 added another attribute for this function to return: main_idea_accuracy
def populate_pyramid2():
    hrp_location = os.path.join(basedir, "MongoDB/HRP_Files/essay2_pyramid_readable_20230403.pyr")
    # must cast the pyramid_id as float
    pyramid_id = float(20230403)
    pyramid_name = "essay2_pyramid_readable_20230403"
    essay_number = 2
    essay_main_ideas = ["1", "2", "3", "4", "5", "6","7","8"]
    scu_mapping = ["5", "0", "4", "2", "1", "3","6","7"]
    main_idea_accuracy = {
        "high_acc": ["4", "6"],
        "med_acc": ["1", "2", "3"],
        "low_acc": ["5", "7", "8"]
    }

    return hrp_location, pyramid_id, pyramid_name, essay_number, essay_main_ideas, scu_mapping, main_idea_accuracy


if __name__ == "__main__":
    # Added 4/05/23 by MS
    parser = argparse.ArgumentParser(description='Pyramid2 or Pyramid1')
    parser.add_argument('--pyramidNumber', required=True, type=int)
    args = parser.parse_args()

    # Becky 4/7/23 added the main_idea_accuracy attribute here for both pyramids
    if args.pyramidNumber == 1:
        hrp_location, pyramid_id, pyramid_name, essay_number, essay_main_ideas, scu_mapping, main_idea_accuracy = populate_pyramid1()
    elif args.pyramidNumber == 2:
        hrp_location, pyramid_id, pyramid_name, essay_number, essay_main_ideas, scu_mapping, main_idea_accuracy = populate_pyramid2()

    # Code to connect to the databse
    mongodb_operations.connect(database_name);

    mongodb_operations.populate_pyramids(pyramid_id, pyramid_name, hrp_location)

    # Added 2/17/23 to ensure that the essay_main_ideas to scu_mapping and the essay number are populated in the db along with the pyramid that is read in
    # Updated 4/7/23 to input main_ideas_accuracy here rather than in mongo_db_functions
    mongodb_operations.populate_essay_pyramid(pyramid_id, essay_number, essay_main_ideas, scu_mapping, main_idea_accuracy)
