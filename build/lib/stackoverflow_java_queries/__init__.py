import os
import re
import pandas as pd
import javalang
from google.cloud import bigquery

class codeExtractor():

    def __init__(self,dataset=None,path=None):
        """
        Code Extractor Constructor - Recieves a dataset or path to a csv file and keeps the data as in Attribute.
        """
        if path == None:
            self.data = dataset
        else: self.data = pd.read_csv(path)

    def extractCodes(self):
        """
        extractCodes Function - cleans the dataset by removing unnecessary tags like <p> and keeps <code> tags.
        Return - dictionary -> title : codeslist
        """
        new_data = self.data['body']
        index = 0
        code_dict = {}
        for data in new_data:
            code = []
            row = re.sub('<p>.*?</p>', '', data)
            for curr_code in re.findall(r"<code>(.*?)</code>", row, flags=re.DOTALL):
                code.append(curr_code)
            code_dict[self.data['title'][index]] = code
            index+=1
        return code_dict

class codeParser():

    def __init__(self,code_dict):
        """
        Code Parser Constructor - receives dataset of codes, and parse the code to fields.
        """
        self.all_codes = code_dict
        self.counter_succeded_queries = 0

    def parse_code(self):
        """
        parseCode Function - Parse each query and each code inside the query code list.
        """
        for title in self.all_codes:

            for code in self.all_codes[title]:
                self.code_parser(code,title)
        #orint the counted posts
        #print(self.counter_succeded_queries)

    def code_parser(self,code,title):
        """
        code_parser Function - Parse the received code using javalang parser, separate each field and prints the codes fields
        """
        field_names = []
        method_names = []
        class_names = []
        try:
            tree = javalang.parse.parse(code)
        except :
            return
        print("Query Title:", title)
        print("#####################################")

        for class_extract in tree.types:
            self.counter_succeded_queries += 1
            print(str(class_extract.name)," - Class")
            class_names.append(class_extract.name)
            if (isinstance(class_extract, javalang.tree.ClassDeclaration)):
                for constructor in class_extract.constructors:
                    if (isinstance(constructor, javalang.tree.ConstructorDeclaration)):
                        constructor_name = constructor.name
                for field in class_extract.fields:
                    if (isinstance(field, javalang.tree.FieldDeclaration)):
                        for declare in field.declarators:
                            print(declare.name," - Attribute")
                            field_names.append(declare.name)
                for method in class_extract.methods:
                    print(method.name," - Operation")
                    method_names.append(str(method.name))
            print("-------------------------------------")



class dataCollector():

    def __init__(self,path):
        """
        Data Collector Constructor - adds google credentials.
        """
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=(path)

    def openclient(self):
        """
        openclient Function - connects to google big query dataset
        """
        self.client = bigquery.Client()
        self.dataset_ref = self.client.dataset("stackoverflow", project="bigquery-public-data")

    def getdataset(self,query):
        """
        getdataset Function - Enters a query to google big query dataset
        Return - dataframe that contains java related posts
        """
        safe_config = bigquery.QueryJobConfig(maximum_bytes_billed=40 ** 10)
        questions_query_job = self.client.query(query, job_config=safe_config)
        questions_results = questions_query_job.to_dataframe()
        questions_results = questions_results[~questions_results.body.isin(['class'])]
        return questions_results