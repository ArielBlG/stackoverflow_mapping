import os
from google.cloud import bigquery

class dataCollector():

    def __init__(self):
        """
        Data Collector Constructor - adds google credentials.
        """
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=('Cred.json')

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