import json
import re
import os
import sys
import inspect
from pathlib import Path

file_path = Path(os.getcwd())
sys.path.append(str(file_path.parent.absolute()) + '/')
import pandas as pd
from CodeMapping import stackoverflow_java_queries
from CodeMapping import MapCreator, ParserToMap, CodeWrapper
from CodeMapping.CodeFromFile import CodeFromFile
from TextMapping import ExtractText
from collections import namedtuple
from os.path import dirname, join

import psutil
import time

from CodeMapping import BigQuery

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
non_working_files_luence = ['TestBKD', 'BaseXYShapeTestCase', 'BaseLatLonShapeTestCase', 'BaseLatLonPointTestCase',
                            'BaseLatLonDocValueTestCase', 'BaseLatLonSpatialTestCase', 'TestIndexWriter',
                            'TestFieldReuse', 'TestDirectory', 'PerFieldPostingsFormat', 'QueryBuilder',
                            'GraphTokenStreamFiniteStrings', 'ExactPhraseMatcher', 'BlendedTermQuery', 'SynonymQuery',
                            'DisjunctionScoreBlockBoundaryPropagator', 'IndexUpgrader', 'IndexingChain', 'MergePolicy',
                            'ByteBuffersDataInput', 'ByteBuffersDirectory', 'TableUtils', 'PresetAnalyzerPanelProvider',
                            'CustomAnalyzerPanelProvider', 'QueryParserPaneProvider', 'SortPaneProvider',
                            'AnalysisChainDialogFactory', 'DocValuesDialogFactory', 'IndexOptionsDialogFactory',
                            'SubtypeCollector', 'ClassScanner', 'TestOpenNLPChunkerFilterFactory',
                            'TestOpenNLPPOSFilterFactory', 'TestMemoryIndex', 'CommonTermsQuery', 'LuceneTestCase',
                            'VerifyTestClassNamingConvention', 'BaseDirectoryTestCase', 'CombinedFieldQuery',
                            'OffsetsFromPositions', 'PassageSelector', 'UnifiedHighlighter', 'MissingDoclet']


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
    directory_in_str = "/Users/ariel-pc/Desktop/Package/src"
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/MaximGit/System"
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/lucene-main"
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/src/java/org/apache/poi/"
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/src/java/"
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/lucene-main/lucene/benchmark/src/java/org/apache/lucene/benchmark/byTask/utils/Algorithm.java"
    # directory_in_str = "/Users/ariel-pc/Desktop/Package/lucene-main/lucene/core/src/test/org/apache/lucene/document/BaseXYShapeTestCase.java"

    directory = os.fsencode(directory_in_str)
    code_parser = stackoverflow_java_queries.codeParser()
    text = ""
    pathlist = Path(directory_in_str).glob('**/*.java')
    # pathlist = [directory_in_str]
    non_working = []
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
            # try:
            #     current_query = CodeWrapper.CodeWrapper("test", "test")
            #     mapped_code = code_parser.parse_post(text, current_query)
            # except:
            #     print(path_in_str.split('/')[-1].split('.')[0])
            #     non_working.append(path_in_str.split('/')[-1].split('.')[0])
            #     continue
    current_query = CodeWrapper.CodeWrapper("Lucene", "Lucene")
    mapped_code = code_parser.parse_post(text, current_query)
    # print(non_working)
    map_code = MapCreator.MapCreator(mapped_code)
    # for _class in mapped_code.sub_classes:
    #     if _class.class_name == "workbook":
    #         for _method in _class.Methods:
    #             # if _method.method_name == "getInternalWorkbook":
    #             if "getInternal" in _method.method_name:
    #                 print("a")
        #     elif _method.method_name == "Workbook":
        #         print("b")
    task_dict = map_code.create_dictionary(current_query)
    #key = -13, -1279, -4343
    # from: -1
    # to -15
    # for dic in task_dict["nodeDataArray"]:
    #     if dic['text'] == "workbook":
    #         print("a")
    # for dic in task_dict["linkDataArray"]:
    #     if dic["from"] == -4343 or dic["to"] == -4343:
    #         print("a")
    # print("fa")
    with open("poi_map.json", 'w') as fp:
        json.dump(task_dict, fp)
    # print(task_dict)


if __name__ == "__main__":
    Main2()
    # if sys.argv[1] == "B":
    #     big_query = BigQuery.BigQuery()
    #     big_query.execute()
    # elif sys.argv[1] == "F":
    #     code_from_file = CodeFromFile(file_path=sys.argv[2], name=sys.argv[3], output_path=sys.argv[4])
    #     code_from_file.concat_files()
    #
    # elif sys.argv[1] == "T":
    #     code_from_file = CodeFromFile(file_path=sys.argv[2], name=sys.argv[3], output_path=sys.argv[4])
    #     code_from_file.test_new_file()
