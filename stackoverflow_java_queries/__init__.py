import os
import re
import pandas as pd
import javalang
from google.cloud import bigquery
import CodeWrapper

primitive_types = ['Boolean', 'boolean', 'char', 'byte', 'short', 'int', 'long', 'float', 'double', 'String', 'string',
                   'System', 'System.out', 'Scanner', 'Log']
system_methods = ['System', 'System.out', 'Scanner', 'Log']


class codeExtractor():

    def __init__(self, dataset=None, path=None):
        """
        Code Extractor Constructor - Recieves a dataset or path to a csv file and keeps the data as in Attribute.
        """
        if path == None:
            self.data = dataset
        else:
            self.data = pd.read_csv(path)

    def extractCodes(self):
        """
        extractCodes Function - cleans the dataset by removing unnecessary tags like <p> and keeps <code> tags.
        Return - dictionary -> title : codeslist
        """
        index = 0
        body_df = self.data.drop('answers_body', axis=1)
        answer_df = self.data.drop('body', axis=1)
        body_df = body_df.drop_duplicates(subset=['title'])
        code_dict = pd.DataFrame(columns=['title', 'text', 'code'])
        code_dict = self.extract_code_text(body_df, 0, code_dict, " - Post", 'body')
        code_dict = self.extract_code_text(answer_df, 0, code_dict, " - Answer", 'answers_body')

        code_dict = code_dict.sort_values(by=['title'])

        code_dict.to_csv('mycodecsv.csv')
        return code_dict

    def extract_code_text(self, data_df, index, code_dict, answer_post, column):
        for index, df_row in data_df.iterrows():
            code = []
            text = []

            for curr_text in re.findall(r"<p>(.*?)</p>", df_row[column], flags=re.DOTALL):
                text.append(curr_text)
            # code_dict['text'][index] = text
            row = re.sub('<p>.*?</p>', '', df_row[column])
            for curr_code in re.findall(r"<code>(.*?)</code>", row, flags=re.DOTALL):
                curr_code = curr_code.replace('&gt;', '>')
                curr_code = curr_code.replace('&lt;', '<')
                code.append(curr_code)
            ##TODO: if code == null
            title = df_row['title'] + answer_post
            df2 = pd.DataFrame([[title, text, code]], columns=['title', 'text', 'code'])
            code_dict = pd.concat([df2, code_dict])
            index += 1

        return code_dict


class codeParser():

    def __init__(self, code_dict):
        """
        Code Parser Constructor - receives dataset of codes, and parse the code to fields.
        """
        self.all_codes = code_dict
        self.counter_succeded_queries = 0
        self.mapped_code = []

    def parse_code(self):
        """
        parseCode Function - Parse each query and each code inside the query code list.
        """

        for index, row in self.all_codes.iterrows():
            # TODO: fix not working queries
            current_query = CodeWrapper.CodeWrapper(row['title'], row['text'])
            self.mapped_code.append(current_query)

            for code in row['code']:
                self.code_parser(code, row['title'], current_query)

        # print(self.counter_succeded_queries)
        return self.mapped_code

    def code_parser(self, code, title, current_query):
        """
        code_parser Function - Parse the received code using javalang parser, separate each field and prints the codes fields
        """

        try:
            tree = javalang.parse.parse(code)
        except:
            # self.remove_query(current_query)
            return
        """add a new map object"""
        # self.counter_succeded_queries += 1

        # TODO: fix the url
        # current_query.find_url()

        print("Query Title:", title)
        print("#####################################")

        for class_extract in tree.types:
            """adds the calls name and create task object"""
            current_class = CodeWrapper.ClassTask(class_extract.name)
            current_query.add_class(current_class)

            """extract class comments"""
            if class_extract.documentation is not None:
                for documentation in class_extract.documentation:
                    current_class.set_documentation(documentation)

            if not isinstance(class_extract, javalang.tree.AnnotationDeclaration):

                """adds implements classes"""
                if not isinstance(class_extract,
                                  javalang.tree.InterfaceDeclaration) and class_extract.implements is not None:
                    for implement_class in class_extract.implements:
                        self.add_implemented_class(current_query, implement_class, current_class)

                """adds the extended class's"""
                if not isinstance(class_extract, javalang.tree.EnumDeclaration) and class_extract.extends is not None:
                    if not isinstance(class_extract.extends, list):
                        self.add_extended_class(current_query, class_extract.extends, current_class)
                    else:
                        for class_extend in class_extract.extends:
                            self.add_extended_class(current_query, class_extend, current_class)

            """adds the constructor to the task"""
            if isinstance(class_extract, javalang.tree.ClassDeclaration):
                for constructor in class_extract.constructors:
                    if isinstance(constructor, javalang.tree.ConstructorDeclaration):
                        self.extract_constructor(constructor, current_class)

                """adds the class attributes to the task"""
                for field in class_extract.fields:
                    if isinstance(field, javalang.tree.FieldDeclaration):
                        for declare in field.declarators:
                            self.add_attributes(current_class, declare, current_query, field.type.name)

                """adds the class methods to the task"""
                for method in class_extract.methods:
                    current_method = CodeWrapper.MethodTask(method.name, current_class)
                    current_class.add_class_methods(current_method)

                    """adds the method comments"""
                    if method.documentation is not None:
                        for documentation in method.documentation:
                            current_method.set_documentation(documentation)

                    """add method parameters for function calls"""
                    self.extract_method_parameters(method.parameters, current_method, current_query)

                """handle method function calls"""
                for method in class_extract.methods:
                    current_method = current_class.get_class_method(method.name)
                    self.extract_method_invocation(method.children, current_query, current_method)

            # self.print_map(current_query)
            print("-------------------------------------")

    def add_implemented_class(self, current_query, implement_class, current_class):
        """
        add_implemented_class Function - adds all implemented class of the current class
        :param current_query:
        :param implement_class:
        :param current_class:
        """
        implement_class_new = current_query.get_class(implement_class.name)

        """checks if the implemented class is already mapped"""
        if implement_class_new is None:
            implement_class_new = CodeWrapper.ClassTask(implement_class.name)
            current_query.add_class(implement_class_new)

        current_class.add_implement_class(implement_class_new)

    def add_extended_class(self, current_query, extended_class, current_class):
        """
        add_extended_class Funciton - adds the extended class of the current class
        :param current_query:
        :param extended_class:
        :param current_class:
        :return:
        """

        extended_class_new = current_query.get_class(extended_class.name)

        """checks if the extended class is already mapped"""
        if extended_class_new is None:
            extended_class_new = CodeWrapper.ClassTask(extended_class.name)
            current_query.add_class(extended_class_new)

        current_class.add_extended_class(extended_class_new)

    def extract_method_invocation(self, children_list, current_query, current_method):
        """
        extract_method_invocation Function - extract the method's function calls recursively
        :param children_list:
        :param method_list:
        :param current_query:
        :param current_method:
        """
        for expression in children_list:
            """base case"""
            if isinstance(expression, javalang.tree.Invocation):
                self.connect_methods_to_class(current_method, current_query, expression)

            else:
                """handle list of expressions"""
                if isinstance(expression, list):

                    if len(expression) == 1:
                        self.extract_method_invocation(expression, current_query, current_method)

                    for sub_expression in expression:
                        """handle variable declaration with method invocation"""
                        if isinstance(sub_expression, javalang.tree.LocalVariableDeclaration):
                            attribute_type = sub_expression.type.name
                            for children in sub_expression.children:
                                if isinstance(children, list):
                                    for declare in children:
                                        if isinstance(declare, javalang.tree.VariableDeclarator):
                                            self.extract_method_locals(current_query, attribute_type, children,
                                                                       current_method)

                        if sub_expression is not None and isinstance(sub_expression, javalang.ast.Node):
                            self.extract_method_invocation(sub_expression.children, current_query,
                                                           current_method)
                else:
                    """handle single expression"""
                    if (expression is not None and (
                            isinstance(expression, javalang.tree.Statement) or isinstance(expression,
                                                                                          javalang.tree.Declaration) or isinstance(
                        expression, javalang.tree.Expression))):
                        self.extract_method_invocation(expression.children, current_query, current_method)

    def connect_methods_to_class(self, current_method, current_query, expression):
        """
        connect_methods_to_class Function - connect the function calls to the function task
        :param expression:
        :param current_method:
        :param current_query:
        """

        """handle super constructor call"""
        if isinstance(expression, javalang.tree.SuperConstructorInvocation):
            self.super_constructor_call(current_method)
            return

        qualifier_name = expression.qualifier
        method_name = expression.member

        """checks if the method is already mapped"""
        if current_method.find_method_call(method_name) is not None:
            return

        """handle super calls"""
        if isinstance(expression, javalang.tree.SuperMethodInvocation):
            qualifier = current_method.get_method_super_class().Extends
            if qualifier is None:  # TODO: check if not working
                print("Problem with super class")
                return
            method = qualifier.get_class_method(method_name)
            """checks if the method is updated to super class"""
            if method is None:
                method = CodeWrapper.MethodTask(method_name, qualifier)
                qualifier.add_class_methods(method)

            """handle "this" method calls"""
        elif qualifier_name is None or qualifier_name == "":
            qualifier = current_method.get_method_super_class()
            method = current_method.get_method_super_class().get_class_method(method_name)
            """handle unkown calls"""
            if method is None:
                qualifier = CodeWrapper.ClassTask("unkown")
                current_query.add_class(qualifier)
                method = CodeWrapper.MethodTask(method_name, qualifier)
                qualifier.add_class_methods(method)
                current_method.add_method_calls(method)
                return

        else:
            current_attribute = current_method.get_attribute(qualifier_name)
            """checks if the variable already declared and extract the class task"""
            if current_attribute is not None:
                qualifier = current_attribute.get_attribute_class()
                method = qualifier.get_class_method(method_name)
                if method is None:
                    method = CodeWrapper.MethodTask(method_name, qualifier)
                    qualifier.add_class_methods(method)
            else:
                """checks if the variable name is system call"""
                if qualifier_name not in system_methods:
                    qualifier_class_attribute = current_method.get_method_super_class().get_specific_attribute(
                        qualifier_name)
                    if qualifier_class_attribute is None:  # TODO: check if relevant
                        qualifier = CodeWrapper.ClassTask(qualifier_name)
                        current_query.add_class(qualifier)
                        method = CodeWrapper.MethodTask(method_name, qualifier)
                        qualifier.add_class_methods(method)
                    else:
                        """checks if the called method already declared in the task class"""
                        method = qualifier_class_attribute.get_attribute_class().get_class_method(method_name)
                        if method is None:
                            method = CodeWrapper.MethodTask(method_name, qualifier_class_attribute)
                            qualifier_class_attribute.get_attribute_class().add_class_methods(method)
                else:
                    return
        """update method call"""
        current_method.add_method_calls(method)

    def super_constructor_call(self, current_method):
        qualifier = current_method.get_method_super_class().Extends
        method = CodeWrapper.MethodTask("Super Call", qualifier)
        qualifier.add_class_methods(method)
        current_method.add_method_calls(method)

    def extract_method_parameters(self, parameters, method, current_query):
        """
        extract_method_parameters Function - extract method parameters for the function calls
        :param parameters:
        :param method:
        :param current_query:
        """
        for parameter in parameters:
            """skips primitive parameters"""
            if parameter.type.name in primitive_types:
                continue

            current_class = current_query.get_class(parameter.type.name)
            """checks if the class is already declared"""
            if current_class is not None:
                attribute = CodeWrapper.ClassAttribute(current_class, parameter.name)
                method.add_method_attributes(attribute)
            else:
                # TODO: check the fields objects type
                new_class = CodeWrapper.ClassTask(parameter.type.name)
                current_query.add_class(new_class)
                attribute = CodeWrapper.ClassAttribute(new_class, parameter.name)
                method.add_method_attributes(attribute)

    def extract_constructor(self, constructor, current_class):
        """
        extract_constructor Function - extract constructor of the class
        :param constructor:
        :param current_class:
        :return:
        """
        constructor_name = constructor.name
        constructor = CodeWrapper.MethodTask(constructor_name, current_class)
        current_class.add_class_methods(constructor)
        current_class.add_constructors(constructor)

    def extract_method_locals(self, current_query, declare_type, declarator, current_method):
        """
        extract_method_locals Function - extract method local variables for function calls
        :param current_query:
        :param declare_type:
        :param declarator:
        :param current_method:
        """
        current_class = current_method.get_method_super_class()
        attribute = None
        """skips primitive local declares"""
        if declare_type in primitive_types:
            return

        for declare in declarator:
            """checks if the local is from the same class of method"""
            if declare_type == current_class.get_class_name():
                attribute = CodeWrapper.ClassAttribute(current_class, declare.name)

            elif declare_type not in primitive_types:
                class_to_add = current_query.get_class(declare_type)
                """checks if the variable type class is already declared"""
                if class_to_add is None and class_to_add not in system_methods:
                    new_class = CodeWrapper.ClassTask(declare_type)
                    current_query.add_class(new_class)
                    attribute = CodeWrapper.ClassAttribute(new_class, declare.name)
                    new_class.add_class_attributes(attribute)
                else:
                    attribute = CodeWrapper.ClassAttribute(class_to_add, declare.name)

        current_method.add_method_attributes(attribute)

    def add_attributes(self, current_class, declare, current_query, object_type):
        """
        add_attributes Function - adds the class attributes
        :param current_class:
        :param declare:
        :param current_query:
        :param object_type:
        """
        """"checks if the current variable type is from the same class"""
        if object_type == current_class.get_class_name():
            attribute = CodeWrapper.ClassAttribute(current_class, declare.name)
            if attribute not in current_class.get_class_attributes():
                current_class.add_class_attributes(attribute)
            """skips primitive types"""
        elif object_type not in primitive_types:
            # TODO: check the fields objects type
            class_to_add = current_query.get_class(object_type)
            """checks if the class of the variable is already mapped"""
            if class_to_add is None:
                new_class = CodeWrapper.ClassTask(object_type)
                current_query.add_class(new_class)
                attribute = CodeWrapper.ClassAttribute(new_class, declare.name)
                current_class.add_class_attributes(attribute)
            else:
                attribute = CodeWrapper.ClassAttribute(class_to_add, declare.name)
                current_class.add_class_attributes(attribute)
            """adds the primitive types of the class"""
        else:
            new_class = CodeWrapper.ClassTask(object_type)
            attribute = CodeWrapper.ClassAttribute(new_class, declare.name)
            current_class.add_class_attributes(attribute)

    def print_map(self, current_query):
        for curr_class in current_query.get_queries_class():
            print("Class name:", curr_class.get_class_name())
            for attribute in curr_class.get_class_attributes():
                print("achived by - " + attribute.get_attribute_name())
            print("class methods:")
            for method in curr_class.get_all_method():
                print(curr_class.get_class_name(), "consist of - " + method.get_method_name())
                for call_method in method.get_calling_method():
                    print(method.get_method_name(), "consist of - ", call_method.get_method_name(),
                          " and the class name is: ", call_method.get_method_super_class().get_class_name())

        print("----------------------------------------------------------------------------------------------------")

    def get_query(self, query):
        # TODO: check if relevant
        for temp_query in self.mapped_code:

            if temp_query == query:
                return temp_query
        return None

    def remove_query(self, query_to_remove):
        # TODO: check if relevant
        query = self.mapped_code.pop()
        if len(query.sub_classes) == 0:
            return
        self.mapped_code.append(query)


class dataCollector():

    def __init__(self, path):
        """
        Data Collector Constructor - adds google credentials.
        """
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (path)

    def openclient(self):
        """
        openclient Function - connects to google big query dataset
        """
        self.client = bigquery.Client()
        self.dataset_ref = self.client.dataset("stackoverflow", project="bigquery-public-data")

    def getdataset(self, query):
        """
        getdataset Function - Enters a query to google big query dataset
        Return - dataframe that contains java related posts
        """
        safe_config = bigquery.QueryJobConfig(maximum_bytes_billed=40 ** 10)
        questions_query_job = self.client.query(query, job_config=safe_config)
        questions_results = questions_query_job.to_dataframe()
        questions_results = questions_results[~questions_results.body.isin(['class'])]
        questions_results = questions_results[~questions_results.answers_body.isin(['class'])]
        questions_results.to_csv("question_result.csv")
        return questions_results
