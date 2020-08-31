import javalang
import pandas as pd
import stackoverflow_java_queries
from CodeMapping import MapCreator, MetaDataCollector
import json
import plyj.parser as plyj
import javac_parser
from collections import namedtuple
import os
import csv
TEST_FILENAME = os.path.join(os.path.dirname(__file__), 'Cred.json')
Position = namedtuple('Position', ['line', 'column'])

def extract_temp_mapped(mapped_code):
    query_dict = {}
    for title in mapped_code.keys():
        for post in mapped_code[title]:

            query_dict[title] = post.score
    return query_dict

def Main():
    # the query we send to bigquery datasset, joining question and answer by id
    # filter the limit to 10000 - need better computer for more
    #TODO: , pq.tags
    questions_query = """
                        SELECT pq.title,pq.body, com.body as answers_body, com.score as score, pq.tags as tags
    FROM `bigquery-public-data.stackoverflow.posts_questions` as pq
    inner join `bigquery-public-data.stackoverflow.posts_answers` as com on pq.id = com.parent_id
    WHERE pq.tags LIKE '%java%' AND pq.tags NOT LIKE '%javascript%' AND pq.body LIKE '%<code>%' AND pq.body LIKE '%class%' 
         AND com.body LIKE '%<code>%'
    LIMIT 5000
                      """

    """creates the datacollector"""
    #
    # datacollector = stackoverflow_java_queries.dataCollector(TEST_FILENAME)
    # datacollector.openclient()
    # data_set = datacollector.getdataset(questions_query)  # get the data set created from the bigquery dataset
    # data_set.to_csv('df_score.csv')


    # data_set.to_csv('df2.csv')

    data_set = pd.read_csv('df_score.csv', encoding="ISO-8859-1", nrows=800)
    codeextractor = stackoverflow_java_queries.codeExtractor(data_set)


    body_mapping, answer_mapping = codeextractor.extractCodes()


    """the whole data set"""
    # codeparser = stackoverflow_java_queries.codeParser(codes)
    codeparser = stackoverflow_java_queries.codeParser(body_mapping=body_mapping, answer_mapping=answer_mapping)
    mapped_code = codeparser.parse_code_new()
    query_dict = extract_temp_mapped(mapped_code)
    # {k: v for k, v in sorted(query_dict.items(), key=lambda item: item[1])}
    with open('temp_query.csv', 'w') as f:  # Just use 'w' mode in 3.x
        w = csv.DictWriter(f, query_dict.keys())
        w.writeheader()
        w.writerow(query_dict)
    # map_code = MapCreator.MapCreator(mapped_code)

    # task_dict = map_code.create_dictionary(query='Simple Java calculator')
    # with open("sample_1.json", 'w') as outfile:
    #     json.dump(task_dict[0], outfile)
    # with open("sample_2.json", 'w') as outfile:
    #     json.dump(task_dict[1], outfile)
    # with open("sample_3.json", 'w') as outfile:
    #     json.dump(task_dict[2], outfile)

    # metadata = MetaDataCollector.MetaModel()
    # metadata.create_meta_model()

if __name__ == "__main__":
    Main()
