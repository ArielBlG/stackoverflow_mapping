import copy
import json
from stackoverflow_java_queries import codeParser
from stackoverflow_java_queries import CodeWrapper
from google.cloud import storage
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/ariel-pc/Downloads/stackoverflowmap-03d45ecd6795.json"


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

    def initiate(self):
        """
        initiate Function - initiate the mapping, calls the parser and creates a map, uploads it to cloud
        """
        for query in self.data_frame_iterator():
            mapped_code = self._MapCreator.MapCreator(query).create_dictionary(query)
            json_name = '(' + str(query.score) + ')' + query.query + ".json"
            json_file = json.dumps(mapped_code)
            upload_blob("json_outputs", json_file, json_name)
            #print(json_name)

    def data_frame_iterator(self):
        """
        data_frame_iterator Function - yields the received df and calls the parser connector
        :return: yield finished queries
        """
        for title, body_dict in self._body_mapping.items():
            if title == "Can I get the instance in a method using Guice?":
                print("he")
            # query_yield = self.parser_connector(title, body_dict)
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
        current_query.add_tags(body_dict[2])  # add post tags to query
        # current_query.find_url() # TODO: fix the url
        self._codeParser.parse_post(body_dict, current_query)  # TODO: check if query update worked

        for answer_body_dict in self._answer_mapping[title]:
            copy_query = copy.deepcopy(current_query)  # creates new query instance
            copy_query.add_answer_text(answer_body_dict[0])
            copy_query.add_score(answer_body_dict[2])

            if self._codeParser.parse_answer(answer_body_dict, copy_query):
                yield copy_query
