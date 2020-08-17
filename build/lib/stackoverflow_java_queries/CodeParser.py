import javalang

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