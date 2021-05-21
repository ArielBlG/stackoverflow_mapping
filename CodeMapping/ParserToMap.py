import copy
import json
from stackoverflow_java_queries import codeParser
from stackoverflow_java_queries import CodeWrapper
from google.cloud import storage
import os
from os.path import dirname, join

temp_dir = dirname(dirname(__file__))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = join(temp_dir, 'CodeMapping/stackoverflowmap-03d45ecd6795.json')


def upload_blob(bucket_name, source, destination_blob_name):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(source)


class ParserToMap:
    def __init__(self, map_creator, code_wrapper, body_mapping=None, answer_mapping=None):
        self._MapCreator = map_creator
        self._codeParser = codeParser(body_mapping, answer_mapping)
        self._CodeWrapper = code_wrapper
        self._body_mapping = body_mapping
        self._answer_mapping = answer_mapping
        self.current_answer = 0
        self.words = []

    def initiate(self):
        """
        initiate Function - initiate the mapping, calls the parser and creates a map, uploads it to cloud
        """
        for query in self.data_frame_iterator():
            if not query.sub_classes:
                continue
            mapped_code = self._MapCreator.MapCreator(query).create_dictionary(query)
            # json_name = '(' + str(query.score) + ')' + query.query + str(self.current_answer) + ".json"
            query_name = query.query.replace("/", "")
            # json_name = query_name + "/" + '(' + str(query.score) + ')' + str(self.current_answer) + ".json"
            json_file = json.dumps(mapped_code)
            # upload_blob("new_how_to_json2", json_file, json_name)
            json_name = query_name + str(self.current_answer) + ".json"

            path = dirname(dirname(__file__)) + "/json_maps/" + json_name
            file = open(path, 'w+')
            file.write(json_file)
            file.close()
            # # print("ok")

            # if query.query == "How to sort alphabetically while ignoring case sensitive?":
            #     with open('result.json', 'w') as fp:
            #         json.dump(mapped_code, fp)
            # print(json_name)

    def data_frame_iterator(self):
        """
        data_frame_iterator Function - yields the received df and calls the parser connector
        :return: yield finished queries
        """
        for title, body_dict in self._body_mapping.items():
            self.current_answer = 0
            for query in self.parser_connector(title, body_dict):
                yield query

    def parser_connector(self, title, body_dict):
        """
        parser_connector Function - connects the data frame with the parser
        :param title:
        :param body_dict:
        :return: yield finished queries
        """
        current_query = self._CodeWrapper.CodeWrapper(title, body_dict[0])  # create the query
        # current_query.set_code(body_dict[1])  # add post code to query

        current_query.set_tags(body_dict[2])  # add post tags to query
        current_query.set_id(body_dict[3])

        """handle url"""
        new_url = "https://stackoverflow.com/questions/" + str(body_dict[3]) + "/"
        title_url = title.replace(" ", "-")
        new_url += title_url
        current_query.set_url(new_url)
        self._codeParser.parse_post(body_dict, current_query)  # TODO: check if query update worked

        for answer_body_dict in self._answer_mapping[title]:
            copy_query = copy.deepcopy(current_query)  # creates new query instance
            copy_query.add_answer_text(answer_body_dict[0])
            copy_query.set_score(answer_body_dict[2])

            if self._codeParser.parse_answer(answer_body_dict, copy_query):
                yield copy_query
            self.current_answer += 1
