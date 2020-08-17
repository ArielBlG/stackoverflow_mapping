import re
import pandas as pd

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