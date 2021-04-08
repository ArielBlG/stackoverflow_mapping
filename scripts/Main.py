import json
import re

import pandas as pd
import stackoverflow_java_queries
from CodeMapping import MapCreator, ParserToMap, CodeWrapper
from TextMapping import ExtractText
from collections import namedtuple
from os.path import dirname, join
import os
from pathlib import Path
import psutil
import time

temp_dir = dirname(dirname(__file__))
CRED_FILENAME = join(temp_dir, 'Cred.json')
non_working_files = ["module-info", "TestNotesText", "TestRichTextRun", "TestNameIdChunks", "PAPAbstractType",
                     "TAPAbstractType", "PPDrawing", "HSLFFill", "HemfGraphics", "DrawPaint", "ExtSSTRecord",
                     "SelectionRecord", "FeatRecord", "MergeCellsRecord", "ColorGradientFormatting",
                     "IconMultiStateFormatting"
                     "ChartTitleFormatRecord", "ChartFRTInfoRecord", "ExtRst", "PageItemRecord", "EmbeddedExtractor",
                     "Frequency", "ForkedEvaluator", "ChunkedCipherOutputStream", "StandardEncryptor",
                     "POIFSDocumentPath", "PackagePart", "PackageRelationshipCollection", "PackageRelationshipTypes"
                                                                                          "PackagingURIHelper",
                     "ContentTypes", "PackageNamespaces", "ZipPackage", "OPCPackage", "PackagePartCollection",
                     "UnmarshallContext", "POIXMLFactory", "POIXMLDocument", "POIXMLDocumentPart",
                     "POIXMLExtractorFactory", "XWPFRelation", "XWPFDocument", "XSSFRelation", "XSSFWorkbook"
                                                                                               "SignatureConfig",
                     "OOXMLSignatureFacet", "XAdESSignatureFacet", "RelationshipTransformService", "XDGFRelation",
                     "XSLFSlide", "XSLFRelation", "XSLFGraphicFrame", "XSLFPictureShape", "XSLFSimpleShape",
                     "MergePresentations", "BarChartDem", "TestPageSettingsBlock", "TestHSSFEventFactory"
                                                                                   "TestHSSFSheetUpdateArrayFormulas",
                     "TestHSSFSheet", "TestDateFormatConverter", "TestPropertySorter", "TestEscherContainerRecord",
                     "TestSignatureInfo", "XSLFSimpleShape", "IconMultiStateFormatting", "ChartTitleFormatRecord",
                     "PackageRelationshipTypes", "PackagingURIHelper", "POIXMLRelation", "XSSFWorkbook",
                     "SignatureConfig", "TestSlide", "TestPackage", "TestPackageThumbnail", "TestListParts",
                     "TestContentTypeManager", "TestOPCComplianceCoreProperties", "TestXWPFTableCell",
                     "TestXSSFImportFromXML", "TestXSSFDataValidationConstraint", "TestXSSFDrawing", "TestXSLFNotes",
                     "TestXSLFSlide", "TestXSLFPictureShape", "BarChartDemo", "TestHSSFEventFactory",
                     "TestHSSFSheetUpdateArrayFormulas", "TestXSLFChart", "XMLSlideShow"]

def Main():
    # ext_txt = ExtractText.ExtractText()
    # ext_txt.temp_func()
    # the query we send to bigquery dataset, joining question and answer by id
    # filter the limit to 10000 - need better computer for more
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
    """creates the collector"""
    #
    # questions_query += """and pq.title LIKE '%How do I implement a Hashtable using a Binary Search Tree?%'"""
    data_collector = stackoverflow_java_queries.dataCollector(CRED_FILENAME)
    data_collector.open_client()
    data_set = data_collector.get_dataset(how_to_query)  # get the data set created from the bigquery dataset
    # data_set.to_csv('df_score_id.csv')

    # data_set.to_csv('df2.csv')
    # data_set = pd.read_csv(join(temp_dir, 'temp_datasets/hand_queries.csv'), encoding="ISO-8859-1", nrows=20)
    data_set.columns = ['title', 'body', 'answers_body', 'post_id', 'score', 'tags']
    code_extractor = stackoverflow_java_queries.codeExtractor(data_set)
    # #
    body_mapping, answer_mapping = code_extractor.extractCodes()
    print(len(code_extractor.words))
    file = open("my_text.txt", 'w')
    for text in code_extractor.all_text:
        file.write(text)
    file.close()
    # init = ParserToMap.ParserToMap(MapCreator, CodeWrapper, body_mapping, answer_mapping)
    # init.initiate()

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


def Main2():
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/src/java/org/apache/poi/util/"
    directory_in_str = "/Users/ariel-pc/Desktop/Package/src/"

    directory = os.fsencode(directory_in_str)
    code_parser = stackoverflow_java_queries.codeParser()
    text = ""
    pathlist = Path(directory_in_str).glob('**/*.java')
    counter = 0
    for path in pathlist:
        # because path is object not string
        # text = ""
        path_in_str = str(path)
        if path_in_str.split('/')[-1].split('.')[0] in non_working_files:
            continue
        # print(path_in_str)
        with open(path_in_str, "r") as f:
            # print(path_in_str)
            text += f.read()
            text = re.sub("package(.*?);", '', text)
            text = re.sub("import(.*?);", '', text)
    current_query = CodeWrapper.CodeWrapper("test", "test")
    mapped_code = code_parser.parse_post(text, current_query)
    counter += 1
    map_code = MapCreator.MapCreator(mapped_code)
    task_dict = map_code.create_dictionary(current_query)
    with open("apache_map.json", 'w') as fp:
        json.dump(task_dict, fp)
    print(task_dict)

    # text = re.sub("package(.*?);", '', text)
    # text = re.sub("import(.*?);", '', text)
    # current_query = CodeWrapper.CodeWrapper("test", "test")
    # mapped_code = code_parser.parse_post(text, current_query)
    # map_code = MapCreator.MapCreator(mapped_code)
    # task_dict = map_code.create_dictionary(current_query)
    # print(task_dict)
    # for file in os.listdir(directory):
    #     filename = os.fsdecode(file)
    #     if filename.endswith(".java"):
    #         # text = ""
    #         with open(directory_in_str + filename, "r") as f:
    #             # print(filename)
    #             text += f.read()
    #             # text = f.read()
    #             # current_query = CodeWrapper.CodeWrapper("test", "test")
    #             # code_parser.parse_post(text, current_query)
    #         # print(os.path.join(directory, filename))
    #         continue
    #     else:
    #         continue
    #
    # # df = pd.DataFrame(columns=['title', 'code'])
    # text = re.sub("package(.*?);", '', text)
    # text = re.sub("import(.*?);", '', text)
    # current_query = CodeWrapper.CodeWrapper("test", "test")
    # mapped_code = code_parser.parse_post(text, current_query)
    # map_code = MapCreator.MapCreator(mapped_code)
    # task_dict = map_code.create_dictionary(current_query)
    # print(task_dict)


if __name__ == "__main__":
    Main2()
    # start_time = time.time()
    # Main()
    # print("--- %s seconds ---" % (time.time() - start_time))
    # process = psutil.Process(os.getpid())
    # print(str(process.memory_info().rss) + " Bytes")
