import pandas as pd
import stackoverflow_java_queries
from CodeMapping import MapCreator, ParserToMap, CodeWrapper
from collections import namedtuple
from os.path import dirname, join
import os
import psutil


temp_dir = dirname(dirname(__file__))
CRED_FILENAME = join(temp_dir, 'Cred.json')
import time


def extract_temp_mapped(mapped_code):
    query_dict = {}
    for title in mapped_code.keys():
        for post in mapped_code[title]:
            query_dict[title] = post.score
    return query_dict


def Main():
    # the query we send to bigquery dataset, joining question and answer by id
    # filter the limit to 10000 - need better computer for more
    # TODO: , pq.tags
    questions_query = """
                        SELECT pq.title,pq.body, com.body as answers_body, pq.id as post_id, com.score as score, pq.tags as tags
    FROM `bigquery-public-data.stackoverflow.posts_questions` as pq
    inner join `bigquery-public-data.stackoverflow.posts_answers` as com on pq.id = com.parent_id
    WHERE pq.tags LIKE '%java%' AND pq.tags NOT LIKE '%javascript%' AND pq.body LIKE '%<code>%'
     AND pq.body LIKE '%class%' AND com.body LIKE '%<code>%'
    LIMIT 15
                      """
    how_to_query = """SELECT pq.title,pq.body, com.body as answers_body, pq.id as post_id, com.score as score, pq.tags as tags
        FROM `bigquery-public-data.stackoverflow.posts_questions` as pq
        inner join `bigquery-public-data.stackoverflow.posts_answers` as com on pq.id = com.parent_id
        WHERE pq.tags LIKE '%java%' AND pq.tags NOT LIKE '%javascript%' AND pq.body LIKE '%<code>%'
        AND pq.body LIKE '%class%' AND com.body LIKE '%<code>%' AND pq.title LIKE '%How to%'
        AND (pq.title LIKE '%ist%' OR pq.title LIKE '%ree%' OR pq.title LIKE '%raph%' OR pq.title LIKE '%rray%' OR pq.title LIKE '%sort%' 
        or pq.title LIKE '%queue%' or pq.title LIKE '%stack%' or pq.title LIKE '%DFS%' or pq.title LIKE '%BFS%')
        AND pq.id in (SELECT com1.parent_id
        FROM `bigquery-public-data.stackoverflow.posts_questions` as pq1
        inner join `bigquery-public-data.stackoverflow.posts_answers` as com1 on pq1.id = com1.parent_id
        GROUP BY com1.parent_id
        HAVING COUNT(com1.parent_id) > 3);"""
    """creates the collector"""
    #
    data_collector = stackoverflow_java_queries.dataCollector(CRED_FILENAME)
    data_collector.open_client()
    data_set = data_collector.get_dataset(how_to_query)  # get the data set created from the bigquery dataset
    # data_set.to_csv('df_score_id.csv')

    # data_set.to_csv('df2.csv')
    # data_set = pd.read_csv(join(temp_dir, 'temp_datasets/df_score_id.csv'), encoding="ISO-8859-1", nrows=5000)
    code_extractor = stackoverflow_java_queries.codeExtractor(data_set)
    #
    body_mapping, answer_mapping = code_extractor.extractCodes()
    init = ParserToMap.ParserToMap(MapCreator, CodeWrapper, body_mapping, answer_mapping)
    init.initiate()

    """the whole data set"""
    # code_parser = stackoverflow_java_queries.codeParser(codes)
    # code_parser = stackoverflow_java_queries.codeParser(body_mapping=body_mapping, answer_mapping=answer_mapping)
    # mapped_code = code_parser.parse_code_new()
    # query_dict = extract_temp_mapped(mapped_code)
    # {k: v for k, v in sorted(query_dict.items(), key=lambda item: item[1])}
    # map_code = MapCreator.MapCreator(mapped_code)
    # task_dict = map_code.create_dictionary(query='How to print binary tree diagram?')
    # with open("sample_1.json", 'w') as outfile:
    #     json.dump(task_dict[3], outfile)
    # with open("sample_2.json", 'w') as outfile:
    #     json.dump(task_dict[5], outfile)
    # with open("sample_3.json", 'w') as outfile:
    #     json.dump(task_dict[8], outfile)
    # with open("sample_4.json", 'w') as outfile:
    #     json.dump(task_dict[11], outfile)

    # metadata = MetaDataCollector.MetaModel()
    # metadata.create_meta_model()


if __name__ == "__main__":
    start_time = time.time()
    Main()
    print("--- %s seconds ---" % (time.time() - start_time))
    process = psutil.Process(os.getpid())
    print(str(process.memory_info().rss) + " Bytes")