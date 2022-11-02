# Written by: Adithya Tanam
# Last Update: 10/29/22

class result_data():
    no_of_segments = None
    pyramid_name = None
    raw = None
    max_score = None
    quality = None
    avg_scu = None
    max_score_avg_scu = None
    coverage = None
    comprehensive = None
    content_unit_list = None


class sentence_match_object():
    sentence = None
    segmentation = None

    segment_id = None
    content_unit = None
    weight = None
    segment = {}
    content_unit_sentences = {}

    segments_dict = {}


