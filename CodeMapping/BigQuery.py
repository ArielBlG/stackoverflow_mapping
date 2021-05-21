import stackoverflow_java_queries
from os.path import dirname, join
from CodeMapping import MapCreator, ParserToMap, CodeWrapper
from CodeMapping import ParserToMap

questions_query = """
                    SELECT pq.title,pq.body, com.body as answers_body, pq.id as post_id, com.score as score,
                     pq.tags as tags, pq.view_count
FROM `bigquery-public-data.stackoverflow.posts_questions` as pq
inner join `bigquery-public-data.stackoverflow.posts_answers` as com on pq.id = com.parent_id
WHERE pq.tags LIKE '%java%' AND pq.tags NOT LIKE '%javascript%' AND pq.body LIKE '%<code>%'
 AND pq.body LIKE '%class%' AND com.body LIKE '%<code>%' 
ORDER BY pq.view_count  DESC
 LIMIT 20000
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
temp_dir = dirname(dirname(__file__))
CRED_FILENAME = join(temp_dir, 'Cred.json')


class BigQuery:
    def __init__(self):
        pass

    def execute(self):
        data_collector = stackoverflow_java_queries.dataCollector(CRED_FILENAME)
        data_collector.open_client()
        data_set = data_collector.get_dataset(how_to_query)  # get the data set created from the bigquery dataset
        data_set.columns = ['title', 'body', 'answers_body', 'post_id', 'score', 'tags']
        code_extractor = stackoverflow_java_queries.codeExtractor(data_set)
        # #
        body_mapping, answer_mapping = code_extractor.extractCodes()

        init = ParserToMap.ParserToMap(MapCreator, CodeWrapper, body_mapping, answer_mapping)
        init.initiate()
