import json
import os
from pathlib import Path
import re

from CodeMapping import stackoverflow_java_queries
from CodeMapping.CodeWrapper import CodeWrapper
from CodeMapping.MapCreator import MapCreator

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

class CodeFromFile:
    def __init__(self, file_path, name='test', output_path=""):
        self.file_path = file_path
        self.directory = os.fsencode(self.file_path)
        self.name = name
        self.output_path = output_path
        self.full_code_text = ""
        self.code_parser = stackoverflow_java_queries.codeParser()

    def concat_files(self):
        pathlist = Path(self.file_path).glob('**/*.java')
        for path in pathlist:
            # because path is object not string
            path_in_str = str(path)
            if path_in_str.split('/')[-1].split('.')[0] in non_working_files:
                continue
            # print(path_in_str)
            with open(path_in_str, "r") as f:
                # print(filename)
                self.full_code_text += f.read()
                self.full_code_text = re.sub("package(.*?);", '', self.full_code_text)
                self.full_code_text = re.sub("import(.*?);", '', self.full_code_text)

                # code_parser.parse_post(text, current_query)
                self.create_parse_and_map()

    def create_parse_and_map(self):
        current_query = CodeWrapper(self.name, self.name)
        mapped_code = self.code_parser.parse_post(self.full_code_text, current_query)
        map_code = MapCreator(mapped_code)
        task_dict = map_code.create_dictionary(current_query)
        if not self.output_path:
            self.output_path = "output_json.json"
        with open(self.output_path, 'w') as fp:
            json.dump(task_dict, fp)
