from os.path import dirname, join
from os import environ
import re
import pandas as pd
import javalang
from google.cloud import bigquery
from CodeMapping import CodeWrapper
from collections import namedtuple
from itertools import takewhile
from enum import Enum
import javac_parser
import copy


class Errors(Enum):
    FAILED_PARSING = 1
    PYTHON_EXCEPTION = 2


Position = namedtuple('Position', ['line', 'column'])
PATH = dirname(__file__)
temp_dir = dirname(dirname(__file__))

Body_Dict = namedtuple('Body_Dict', ['text', 'code', 'tags'])
Post_Dict = namedtuple('post_dict', ['text', 'code', 'score'])

primitive_types = ['Boolean', 'boolean', 'char', 'byte', 'short', 'int', 'long', 'float', 'double', 'String', 'string',
                   'System', 'System.out', 'Scanner', 'Log']


class codeExtractor():

    def __init__(self, dataset=None, path=None):
        """
        Code Extractor Constructor - Recieves a dataset or path to a csv file and keeps the data as in Attribute.
        """
        if path is None:
            # self.data = dataset

            """splits the data frame into body and answers"""
            self.body_df = dataset[["title", "body", "tags"]]
            self.answer_df = dataset[["title", "answers_body", "score"]]
            self.body_df = self.body_df.drop_duplicates(subset=['title'])
            self.body_mapping = {}
            self.answer_mapping = {}
        else:
            self.data = pd.read_csv(path)

    def extractCodes(self):
        """
        extractCodes Function - cleans the dataset by removing unnecessary tags like <p> and keeps <code> tags.
        Return - dictionary -> title : codeslist
        """
        # body_mapping = {}
        # answer_mapping = {}
        # index = 0
        # code_dict = pd.DataFrame(columns=['title', 'text', 'code'])

        """handle the posts"""
        for index, df_row in self.body_df.iterrows():
            try:
                text, code = self.extract_code_text_to_dict(df_row['body'])
            except:
                continue

            if pd.notna(df_row['tags']):
                tags = df_row['tags'].split('|')  # extract the tags

            body_dict = Body_Dict(text, code, tags)  # adds everything to the new dict
            self.body_mapping[df_row['title']] = body_dict
            self.answer_mapping[df_row['title']] = []  # prepare the title to the answer

        """handle the answers"""
        for index, df_row in self.answer_df.iterrows():
            try:
                text, code = self.extract_code_text_to_dict(df_row['answers_body'])
            except:
                continue
            body_dict = Post_Dict(text, code, df_row['score'])  # adds the comment score
            self.answer_mapping[df_row['title']].append(body_dict)

        return self.body_mapping, self.answer_mapping

    def extract_code_text_to_dict(self, post):
        """
        extract_code_text_to_dict Function - extract the code and the text from each post
        :param post:
        :return text, code after the data preprocess
        """
        text = ""
        code = []

        for curr_text in re.findall(r"<p>(.*?)</p>", post, flags=re.DOTALL):  # extract the text
            text += curr_text

        row = re.sub('<p>.*?</p>', '', post)  # remove the text

        for curr_code in re.findall(r"<code>(.*?)</code>", row, flags=re.DOTALL):  # extract the code
            """handle html tags from crawler"""
            curr_code = curr_code.replace('&gt;', '>')
            curr_code = curr_code.replace('&lt;', '<')
            curr_code = curr_code.replace('&amp;&amp;', '&&')
            curr_code = curr_code.replace('&amp;', '&')
            curr_code = curr_code.replace('&quot;', '"')
            curr_code = curr_code.replace('...', '/** ...*/')
            code.append(curr_code)

        # for code_comments in code:
        #     search_comments = re.findall("//(.*?)\n", code_comments, flags=re.DOTALL)
        #     for comment in search_comments:
        #         code = code.replace("//" + comment, '\**' + comment + "*/")

        return text, code


# ------------------------------------------------------------------------------

def extract_specific_code(position, parser_token_list, obj, current_query, modifiers=None):
    """
    extract_specific_code Function - extract code from parse tree
    :param current_query:
    :param obj:
    :param position:
    :param parser_token_list:
    :param modifiers:
    :return: code - txt represents the code of the specific object
    """
    current_query.changed_code()  # notify that code has been changed
    start_index = 0

    """find the start index in the token list"""
    for token in parser_token_list:
        if token.position == position:
            break
        start_index += 1

    """fix start index in the token list before the modifiers"""
    if modifiers is not None:
        while start_index > 0 and position[0] == parser_token_list[start_index].position[0]:
            start_index -= 1
        if start_index != 0:
            start_index += 1
        col_position = parser_token_list[start_index].position[1]
    else:
        col_position = position[1]

    """find the end index in the token list"""
    end_index = start_index + 1
    for index in range(start_index + 1, len(parser_token_list)):
        if parser_token_list[index].position[1] == col_position and parser_token_list[index].value == '}':
            if isinstance(parser_token_list[index], javalang.tokenizer.Separator):
                break
        end_index += 1

    code = javalang.tokenizer.reformat_tokens(parser_token_list[start_index:end_index + 1])  # get the code

    return code


def create_collected_code(query):
    """
    create_collected_code Function - creates a code out of all new changed sub codes
    :param query:
    """

    new_code = ""
    non_changed_classes = []

    if query.imports_codes is not []:
        for _import in query.imports_codes:
            new_code += "import " + _import + ';\n'
    """find which classes have been changed"""
    for sub_class in query.sub_classes:
        if not sub_class.code_changed:
            if sub_class.code is not None:
                new_code += sub_class.code
        else:
            # class_name = sub_class.get_class_name()
            non_changed_classes.append(sub_class)

    """handle the changed classes"""
    for modified_class in non_changed_classes:
        if modified_class.code is None:
            continue
        new_class_code = ""
        new_class_code += modified_class.code.split('{')[0] + "{\n"
        whitespace = list(takewhile(str.isspace, new_class_code))
        "".join(whitespace)
        indent = len(whitespace) + 4
        for class_enum in modified_class.Enums:
            new_class_code += (' ' * indent) + class_enum.code
        for class_atts in modified_class.Attributes:
            if class_atts.code not in new_class_code:
                new_class_code += (' ' * indent) + class_atts.code
        for class_method in modified_class.Methods:
            if class_method.code is not None:
                new_indenet = '\n ' + ' ' * indent
                method_code = class_method.code.replace('\n', new_indenet)
                new_class_code += (' ' * indent) + method_code + '\n '
        new_class_code += (' ' * (indent - 4)) + '}' + '\n'

        modified_class.code = new_class_code
        new_code += modified_class.code
    query.code = new_code


def extract_att_code(position, parser_token_list, current_query, modifiers=None):
    """
    extract_att_code Function - extract the attribute codes
    :param position:
    :param parser_token_list:
    :param current_query:
    :param modifiers:
    :return: code - txt represents the code of the specific attribute
    """
    current_query.changed_code()  # change the attribute code to be changed

    """find the start index"""
    start_index = 0
    for token in parser_token_list:
        if token.position == position:
            break
        start_index += 1

    """fix start index in the token list before the modifiers"""
    if modifiers is not None:
        while start_index > 0 and position[0] == parser_token_list[start_index].position[0]:
            start_index -= 1
        start_index += 1
    # TODO: check if relevant
    #     col_position = parser_token_list[start_index].position[1]
    # else:
    #     col_position = position[1]

    """find the end index in the token list"""
    end_index = start_index + 1
    for index in range(start_index + 1, len(parser_token_list)):
        if parser_token_list[index].position[0] != position[0]:
            break
        end_index += 1

    code = javalang.tokenizer.reformat_tokens(parser_token_list[start_index:end_index])  # get the code

    return code


class codeParser():

    def __init__(self, code_dict=None, body_mapping=None, answer_mapping=None):
        """
        Code Parser Constructor - receives dataset of codes, and parse the code to fields.
        """
        self.all_codes = code_dict
        self.counter_succeded_queries = 0
        self.mapped_code = {}
        self.system_methods = []
        self.parsing_error = None
        # self.java_error_detector = javac_parser.Java()
        self.body_mapping = body_mapping
        self.answer_mapping = answer_mapping
        self.current_parsed = None
        self.java_util_method = []
        self.get_system_methods()
        self.unknown_methods = {}
        self.unknown_attributes = {}

    def get_system_methods(self):
        """
        get_system_methods Function - extract all system methods
        :return:
        """

        """get the java classes name"""
        fin = open(join(temp_dir, 'utils/java_classes_names.txt'), "rt")
        for line in fin:
            line = line.replace('\n', '')
            self.system_methods.append(line)
        fin.close()
        """get the java util classes name"""
        fin = open(join(temp_dir, 'utils/java_util_names.txt'), "rt")
        for line in fin:
            line = line.replace('\n', '')
            self.java_util_method.append(line)
        fin.close()

    def parse_code_new(self):
        """
        parse_code_new Function - main code for code parsing
        :return:
        """

        """handle posts"""
        for title, body_dict in self.body_mapping.items():
            current_query = CodeWrapper.CodeWrapper(title, body_dict[0])  # create the query
            current_query.set_code(body_dict[1])  # add post code to query
            current_query.add_tags(body_dict[2])  # add post tags to query
            # current_query.find_url() # TODO: fix the url

            self.mapped_code[title] = []
            self.current_parsed = "Post"
            for code in body_dict[1]:
                self.code_parser_class(code, current_query)

            """handle answers"""
            for answer_body_dict in self.answer_mapping[title]:
                if "for the input" in answer_body_dict[0]:
                    print("noo")
                copy_query = copy.deepcopy(current_query)
                copy_query.add_answer_text(answer_body_dict[0])
                copy_query.add_score(answer_body_dict[2])
                copy_query.code_changed = False

                self.parsing_error = Errors.FAILED_PARSING
                self.current_parsed = "Answer"

                for answer_code in answer_body_dict[1]:
                    self.code_parser_class(answer_code, copy_query)

                if self.parsing_error is not Errors.FAILED_PARSING and copy_query.code_changed:
                    create_collected_code(copy_query)  # get the working code
                    self.mapped_code[copy_query.query].append(copy_query)

            """check if mapped code succeed"""
            if not self.mapped_code[copy_query.query]:
                self.mapped_code.pop(copy_query.query)

        return self.mapped_code

    def code_parser_class(self, code, current_query):
        """
        code_parser_class Function - trys to parse a class
        :param code:
        :param current_query:
        """
        try:  # trys to parse the code
            tree = javalang.parse.parse(code)
            parser_token_list = javalang.parser.Parser(javalang.tokenizer.tokenize(code)).tokens.list  # token array
            self.parsing_error = None
            if tree.imports:
                self.handle_imports(tree.imports, current_query)
            for class_extract in tree.types:
                self.extractor_class(class_extract, current_query, parser_token_list)

        except (javalang.parser.JavaParserBaseException, javalang.tokenizer.LexerError, TypeError) as e:
            self.code_parser_method(code, current_query)

            """calls java syntax error detect"""
            # if self.parsing_error == Errors.FAILED_PARSING:
            #     print(self.java_error_detector.check_syntax(code))
            # else:
            #     return

    def extractor_class(self, class_extract, current_query, parser_token_list):
        """
        extractor_class Function - extracts everythong from the class
        :param class_extract:
        :param current_query:
        :param parser_token_list:
        """

        """adds the calls name and create task object"""
        current_class = current_query.get_class(class_extract.name)  # checks if the class is already mapped

        if current_class is None:
            current_class = CodeWrapper.ClassTask(class_extract.name)
            current_query.add_class(current_class)

        current_class.set_code(extract_specific_code(class_extract.position, parser_token_list, current_class,
                                                     current_query, modifiers=class_extract.modifiers))

        """adds the class annotation"""
        if class_extract.annotations is not None:
            for annotation in class_extract.annotations:
                current_class.code = extract_att_code(annotation.position, parser_token_list, current_query) + \
                                     current_class.code

        """extract class comments"""
        if class_extract.documentation is not None:
            if isinstance(class_extract.documentation, list):
                for documentation in class_extract.documentation:
                    current_class.set_documentation(documentation)
                    current_class.code = documentation + current_class.code
            else:
                current_class.set_documentation(class_extract.documentation)
                current_class.code = current_class.documentation + '\n ' + current_class.code

        if not isinstance(class_extract, javalang.tree.AnnotationDeclaration):

            """adds implements classes"""
            if not isinstance(class_extract,
                              javalang.tree.InterfaceDeclaration) and class_extract.implements is not None:
                if isinstance(class_extract.implements, list):  # handle multiply implements
                    for implement_class in class_extract.implements:
                        self.add_implemented_class(current_query, implement_class, current_class)
                else:
                    self.add_implemented_class(current_query, class_extract.implements, current_class)
            elif self.current_parsed == "Answer":
                current_class.Implements = []

            """adds the extended class's"""
            if not isinstance(class_extract, javalang.tree.EnumDeclaration) and class_extract.extends is not None:
                if not isinstance(class_extract.extends, list):  # handle multiply extends
                    self.add_extended_class(current_query, class_extract.extends, current_class)
                else:
                    for class_extend in class_extract.extends:
                        self.add_extended_class(current_query, class_extend, current_class)
            elif self.current_parsed == "Answer":
                current_class.Extends = None

        """adds the constructor to the task"""
        self.extractor_class_const(class_extract, parser_token_list, current_class, current_query)

        """adds the class attributes to the task"""
        for field in class_extract.fields:
            attribute = self.extractor_class_atts(field, current_class, current_query, parser_token_list)
            current_class.Attributes += attribute

        """adds the class methods to the task"""
        for method in class_extract.methods:
            current_method = current_class.get_class_method(method.name)  # check if method already mapped

            if current_method is None:
                current_method = CodeWrapper.MethodTask(method.name, current_class)
                current_class.add_class_methods(current_method)
                if self.current_parsed == "Post":  # adds the method from the post
                    current_query.add_methods(current_method)

            current_method.set_code(extract_specific_code(method.position, parser_token_list, current_method,
                                                          current_query, modifiers=method.modifiers))

            self.extractor_method_class(current_method, current_query, method, parser_token_list)

        """handle method function calls"""
        # TODO: problem in method calls
        if class_extract is not None:
            for method in class_extract.methods:
                current_method = current_class.get_class_method(method.name)
                self.extract_method_invocation_new(method, current_query, current_method, parser_token_list)
        else:
            self.extract_method_invocation_new(method, current_query, current_method, parser_token_list)

        """handle enum declarations"""
        for body in class_extract.body:
            if isinstance(body, javalang.tree.EnumDeclaration):
                enum_task = CodeWrapper.EnumTask(body.name, current_class)
                current_class.add_class_enums(enum_task)
                for enum_body in body.body.constants:
                    if isinstance(enum_body, javalang.tree.EnumConstantDeclaration):
                        enum_task.add_enum_const(enum_body.name)
                enum_task.code = extract_specific_code(body.position, parser_token_list, body, current_query,
                                                       body.modifiers)
        """handle sub classes declarations"""
        # TODO: CHECK IF NEEDED TO MAP SAME
        if class_extract is not None:
            for children in class_extract.body:
                if isinstance(children, javalang.tree.ClassDeclaration):
                    self.extractor_class(children, current_query, parser_token_list)

    def extract_method_invocation_new(self, method, current_query, current_method, parser_token_list):
        """
        extract_method_invocation_new Function - extracts the method calls
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        :return:
        """
        if method.body is None:
            return
        for method_body in method.body:
            """handle declarations"""
            if isinstance(method_body, javalang.tree.Declaration):
                self.handle_method_declarations(method_body, method, current_query, current_method, parser_token_list)

            """handle statments"""
            if isinstance(method_body, javalang.tree.Statement):
                self.handle_method_statements(method_body, method, current_query, current_method, parser_token_list)

            """handle expression"""
            if isinstance(method_body, javalang.tree.Expression):
                self.handle_method_expressions(method_body, method, current_query, current_method, parser_token_list)

    def handle_unknown_node(self, node, method, current_query, current_method, parser_token_list):
        """
        handle_unknown_node Function - handles whenever there is unknown node in method body
        :param node:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        """

        """handle declarations"""
        if isinstance(node, javalang.tree.Declaration):
            self.handle_method_declarations(node, method, current_query, current_method, parser_token_list)

        """handle statments"""
        if isinstance(node, javalang.tree.Statement):
            self.handle_method_statements(node, method, current_query, current_method, parser_token_list)

        """handle expression"""
        if isinstance(node, javalang.tree.Expression):
            self.handle_method_expressions(node, method, current_query, current_method, parser_token_list)

    def handle_method_expressions(self, expression, method, current_query, current_method, parser_token_list):
        """
        handle_method_expressions Function - handle expressions in method's body
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        """
        if expression is None:
            return

        # Assignment
        if isinstance(expression, javalang.tree.Assignment):
            self.handle_method_assignment(expression, method, current_query, current_method, parser_token_list)

        # MethodReference
        elif isinstance(expression, javalang.tree.MethodReference):
            expression.method.qualifier = expression.expression.member
            self.handle_self_method_calls(expression.method, method, current_query, current_method)

        # Invocation
        elif isinstance(expression, javalang.tree.Invocation):
            self.handle_method_invokes(expression, method, current_query, current_method)

        # Cast
        elif isinstance(expression, javalang.tree.Cast):
            # raise Exception("not implemented invocations expression")
            self.handle_method_expressions(expression.expression, method, current_query, current_method,
                                           parser_token_list)

        # MemberReference
        elif isinstance(expression, javalang.tree.MemberReference):
            # TODO: check if ok
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        # This
        elif isinstance(expression, javalang.tree.This):
            # TODO: check if ok
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        # Literal
        elif isinstance(expression, javalang.tree.Literal):
            # TODO: check if ok
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        # BinaryOperation
        elif isinstance(expression, javalang.tree.BinaryOperation):
            self.handle_method_expressions(expression.operandl, method, current_query, current_method,
                                           parser_token_list)
            self.handle_method_expressions(expression.operandr, method, current_query, current_method,
                                           parser_token_list)
        # TernaryExpression
        elif isinstance(expression, javalang.tree.TernaryExpression):
            self.handle_method_expressions(expression.condition, method, current_query, current_method,
                                           parser_token_list)
            self.handle_method_expressions(expression.if_false, method, current_query, current_method,
                                           parser_token_list)
            self.handle_method_expressions(expression.if_true, method, current_query, current_method, parser_token_list)

        # ClassCreator
        elif isinstance(expression, javalang.tree.ClassCreator):
            self.handle_method_class_calls(expression, method, current_query, current_method, parser_token_list)

        # ArrayCreator
        elif isinstance(expression, javalang.tree.ArrayCreator):
            # TODO : to complete array creator
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        # ClassReference
        elif isinstance(expression, javalang.tree.ClassReference):
            # TODO : to complete class reference
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        # LambdaExpression
        elif isinstance(expression, javalang.tree.LambdaExpression):
            if isinstance(expression.body, list):
                for body in expression.body:
                    self.handle_unknown_node(body, method, current_query, current_method, parser_token_list)
            else:
                self.handle_unknown_node(expression.body, method, current_query, current_method, parser_token_list)
        # ReferenceType
        elif isinstance(expression, javalang.tree.ReferenceType):
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)
        else:
            print("wa")
            raise Exception("not implemented expression")

    def handle_method_class_calls(self, expression, method, current_query, current_method, parser_token_list):
        """
        handle_method_class_calls Function - map the constructor calls
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        """
        if expression.type.name in self.system_methods:  # skips system methods calls
            return

        for sub_class in current_query.sub_classes:
            if sub_class.class_name == expression.type.name:  # finds the mapped class from call qualifier
                sub_class_const = sub_class.get_class_method(expression.type.name)
                if sub_class_const is None:  # check if constructor exists in the mapped class , else create one
                    sub_class_const = sub_class.get_constructor()
                if sub_class_const is None:
                    sub_class_const = CodeWrapper.MethodTask(sub_class.class_name, sub_class)
                if sub_class_const not in current_method.calling_methods:
                    current_method.add_method_calls(sub_class_const)
                return
        sub_class = CodeWrapper.ClassTask(expression.type.name)
        sub_class_const = CodeWrapper.MethodTask(sub_class.class_name, sub_class)
        if sub_class_const not in current_method.calling_methods:
            current_method.add_method_calls(sub_class_const)

    def handle_method_assignment(self, expression, method, current_query, current_method, parser_token_list):
        """
        handle_method_assignment Function - handles assignment in method's body
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        :return:
        """
        for exp_children in expression.children:
            if isinstance(exp_children, javalang.tree.Expression):
                self.handle_method_expressions(exp_children, method, current_query, current_method, parser_token_list)
            # TODO : check relevent else

    def handle_method_invokes(self, expression, method, current_query, current_method):
        """
        handle_method_invokes Function - handle all the method's invokes
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        """

        # SuperConstructorInvocation
        if isinstance(expression, javalang.tree.SuperConstructorInvocation):
            self.handle_super_const_calls(expression, method, current_query, current_method)

        # SuperMethodInvocation
        elif isinstance(expression, javalang.tree.SuperMethodInvocation):
            self.handle_super_method_calls(expression, method, current_query, current_method)

        # MethodInvocation
        elif isinstance(expression, javalang.tree.MethodInvocation):
            self.handle_self_method_calls(expression, method, current_query, current_method)

        # ClassReference
        elif isinstance(expression, javalang.tree.ClassReference):
            raise Exception("not implemented ClassReference")
        else:
            raise Exception("not implemented invoke")

    def handle_super_const_calls(self, expression, method, current_query, current_method):
        """
        handle_super_const_calls Function - handles the super const calls
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        """
        if expression.qualifier is None:
            current_class = current_method.get_method_super_class()
            if current_class is None or current_class.get_class_name() == "unknown":
                return
            const = current_class.get_constructor()
            if const not in current_method.calling_methods:
                current_method.add_method_calls(const)
        else:
            raise Exception("super constructor with qualifier")

    def handle_self_method_calls(self, expression, method, current_query, current_method):
        """
        handle_self_method_calls Function - handle "this" method invocations
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        """

        """handle second calls"""
        if current_method.find_method_call(expression.member) is not None:
            return
        """handle calls with qualifier"""
        if expression.qualifier is not "":
            qualifier_list = expression.qualifier.split('.')
            call_qualifier = qualifier_list[0]

            if call_qualifier in self.system_methods or call_qualifier in primitive_types:  # check system methods calls
                return

            method_att = current_method.get_attribute(call_qualifier)
            if method_att is None:
                method_att = current_method.get_method_super_class().get_specific_attribute(call_qualifier)
            if method_att is not None:  # gets the class that has the method
                method_att_class = method_att.get_att_obj_type()
                if method_att_class is None:
                    method_att_class = method_att.get_attribute_type()
                if method_att_class is None:
                    raise Exception("problem with declare")
                else:
                    called_method = method_att_class.get_class_method(expression.member)
                    if called_method is None:
                        called_method = CodeWrapper.MethodTask(expression.member, method_att_class)
                    if called_method not in current_method.calling_methods:
                        current_method.add_method_calls(called_method)
                    return  # TODO: change to normal if

                # for sub_class in current_query.sub_classes:
                #     called_method = sub_class.get_class_method(expression.member)
                #     if called_method is not None:
                #         current_method.add_method_calls(called_method)
                #         return  # TODO: change to normal if
            # TODO: be carefull!
            called_method = CodeWrapper.MethodTask(expression.member, call_qualifier)
            if called_method not in current_method.calling_methods:
                current_method.add_method_calls(called_method)
        else:
            if expression.member == current_method.method_name:
                if current_method not in current_method.calling_methods:
                    current_method.add_method_calls(current_method)
            else:
                called_method = current_method.get_method_super_class().get_class_method(expression.member)
                if called_method is not None:
                    if called_method not in current_method.calling_methods:
                        current_method.add_method_calls(called_method)
                else:
                    # TODO: be carefull!
                    called_method = CodeWrapper.MethodTask(expression.member, current_method.get_method_super_class())
                    if called_method not in current_method.calling_methods:
                        current_method.add_method_calls(called_method)
                    current_method.get_method_super_class().add_class_methods(called_method)

    def handle_super_method_calls(self, expression, method, current_query, current_method):
        """
        handle_super_method_calls Function - handle super method calls
        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        """

        current_class = current_method.get_method_super_class()  # get the super class
        if expression.qualifier is None:
            if current_class.Extends is not None:
                extends_class = current_class.Extends
                super_method = extends_class.get_constructor()
                if super_method is None:
                    super_method_task = CodeWrapper.MethodTask(extends_class.class_name, extends_class)
                if super_method_task not in current_method.calling_methods:
                    current_method.add_method_calls(super_method_task)
            elif current_class.Implements is not None:
                if len(current_class.Implements) == 1:
                    impl_class = current_class.Implements[0]
                    super_method = impl_class.get_constructor()
                    if super_method is None:
                        super_method = CodeWrapper.MethodTask(impl_class.class_name, impl_class)
                    if super_method not in current_method.calling_methods:
                        current_method.add_method_calls(super_method)
                else:
                    # TODO: unkown implement
                    # raise Exception("unknown implement")
                    return
        else:
            for class_impl in current_class.Implements:
                if class_impl.class_name == expression.qualifier:
                    impl_class = class_impl
                    break
            super_method = class_impl.get_constructor()
            if super_method is None:
                super_method = CodeWrapper.MethodTask(impl_class.class_name, impl_class)
            if super_method not in current_method.calling_methods:
                current_method.add_method_calls(super_method)

    def handle_method_statements(self, statement, method, current_query, current_method, parser_token_list):
        """
        handle_method_statements Function - handles the method's body statements
        :param statement:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        """

        if statement is None:  # base condition
            return

        # IfStatement
        if isinstance(statement, javalang.tree.IfStatement):
            self.handle_method_expressions(statement.condition, method, current_query, current_method,
                                           parser_token_list)
            self.handle_method_statements(statement.then_statement, method, current_query, current_method,
                                          parser_token_list)
            self.handle_method_statements(statement.else_statement, method, current_query, current_method,
                                          parser_token_list)
        # WhileStatement
        elif isinstance(statement, javalang.tree.WhileStatement):
            self.handle_method_statements(statement.body, method, current_query, current_method, parser_token_list)

        # DoStatement
        elif isinstance(statement, javalang.tree.DoStatement):
            self.handle_method_statements(statement.body, method, current_query, current_method, parser_token_list)
            self.handle_unknown_node(statement.condition, method, current_query, current_method, parser_token_list)

        # ReturnStatement
        elif isinstance(statement, javalang.tree.ReturnStatement):
            self.handle_method_expressions(statement.expression, method, current_query, current_method,
                                           parser_token_list)

        # StatementExpression
        elif isinstance(statement, javalang.tree.StatementExpression):
            self.handle_method_expressions(statement.expression, method, current_query, current_method,
                                           parser_token_list)

        # BlockStatement
        elif isinstance(statement, javalang.tree.BlockStatement):
            for block_statement in statement.statements:
                self.handle_unknown_node(block_statement, method, current_query, current_method, parser_token_list)

        # ForStatement
        elif isinstance(statement, javalang.tree.ForStatement):
            # TODO: didn't handle enhance for statement
            self.handle_method_statements(statement.body, method, current_query, current_method, parser_token_list)

        # TryStatement
        elif isinstance(statement, javalang.tree.TryStatement):
            if statement.block is not None:
                for try_block in statement.block:
                    self.handle_unknown_node(try_block, method, current_query, current_method, parser_token_list)

            if statement.catches is not None:
                for try_catch in statement.catches:
                    self.handle_unknown_node(try_catch, method, current_query, current_method, parser_token_list)

            if statement.finally_block is not None:
                for try_finally in statement.finally_block:
                    self.handle_unknown_node(try_finally, method, current_query, current_method, parser_token_list)

        # CatchClause
        elif isinstance(statement, javalang.tree.CatchClause):
            for catch_block in statement.block:
                self.handle_unknown_node(catch_block, method, current_query, current_method, parser_token_list)

        # ThrowStatement
        elif isinstance(statement, javalang.tree.ThrowStatement):
            self.handle_method_expressions(statement.expression, method, current_query, current_method,
                                           parser_token_list)

        # SwitchStatement
        elif isinstance(statement, javalang.tree.SwitchStatement):
            for switch_cases in statement.cases:
                self.handle_method_statements(switch_cases, method, current_query, current_method, parser_token_list)
            self.handle_method_expressions(statement.expression, method, current_query, current_method,
                                           parser_token_list)

        # SwitchStatementCase
        elif isinstance(statement, javalang.tree.SwitchStatementCase):
            for statements in statement.statements:
                self.handle_unknown_node(statements, method, current_query, current_method, parser_token_list)

        # BreakStatement, ContinueStatement
        elif isinstance(statement, javalang.tree.BreakStatement) or \
                isinstance(statement, javalang.tree.ContinueStatement):
            return
        # TODO: FINISH TEST STATEMENTS
        # AssertStatement

    def handle_method_declarations(self, declarations, method, current_query, current_method, parser_token_list):
        """
        handle_method_declarations Funciton - handles method's body declarations
        :param declarations:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        """

        if isinstance(declarations, javalang.tree.VariableDeclarator):
            raise Exception("not implemented variable decelerator")

        # FieldDeclaration
        elif isinstance(declarations, javalang.tree.FieldDeclaration):
            raise Exception("not implemented field decelerator")

        elif isinstance(declarations, javalang.tree.VariableDeclaration):
            self.handle_variable_decelerator(declarations, method, current_query, current_method, parser_token_list)

        # ConstantDeclaration
        elif isinstance(declarations, javalang.tree.ConstantDeclaration):
            raise Exception("not implemented constant declaration")

        # VariableDeclarator
        elif isinstance(declarations, javalang.tree.VariableDeclarator):
            raise Exception("not implemented local variable decelerator")
        else:
            raise Exception("undefined decelerators")

    def handle_variable_decelerator(self, declarations, method, current_query, current_method, parser_token_list):
        """
        handle_variable_decelerator Function - handle variable decelerator in method's body
        :param declarations:
        :param method:
        :param current_query:
        :param current_method:
        :param parser_token_list:
        """

        current_class = current_method.get_method_super_class()
        if isinstance(declarations, javalang.tree.LocalVariableDeclaration):
            attribute = self.extractor_class_atts(declarations, current_class, current_query, parser_token_list)
            current_method.Attributes += attribute
            for decl in declarations.declarators:
                if isinstance(decl, javalang.tree.VariableDeclarator):
                    if isinstance(decl.initializer, javalang.tree.Expression):
                        self.handle_method_expressions(decl.initializer, method, current_query, current_method,
                                                       parser_token_list)
        else:
            raise Exception("missing variable decelerator")

    def handle_imports(self, code_imports, current_query):
        """
        handle_imports Function - gets the code imports
        :param code_imports:
        :param current_query:
        :return:
        """
        for curr_import in code_imports:
            current_query.add_imports_code(curr_import.path)
            import_value = curr_import.path.split('.')
            if import_value[-1] != "*":
                current_query.add_imports(import_value[-1])

    def code_parser_method(self, code, current_query):
        """
        code_parser_method Function - parse a method instead of class
        :param code:
        :param current_query:
        :return:
        """
        try:
            parser = javalang.parser.Parser(javalang.tokenizer.tokenize(code))
            method = parser.parse_member_declaration()
            parser_token_list = parser.tokens.list
            self.parsing_error = None
        except (javalang.parser.JavaParserBaseException, javalang.tokenizer.LexerError, TypeError, StopIteration) as e:
            # self.parsing_error = Errors.FAILED_PARSING
            return
        """ handles wrong class declaration """
        if isinstance(method, javalang.tree.ClassDeclaration) or isinstance(method, javalang.tree.InterfaceDeclaration):
            self.extractor_class(method, current_query, parser_token_list)

            """ handles single field declaration """
        elif isinstance(method, javalang.tree.FieldDeclaration):
            # TODO: handle method attributes changes
            for declare in method.declarators:
                for sub_class in current_query.sub_classes:
                    attribute = sub_class.get_specific_attribute(declare.name)
                    if attribute is not None:
                        attribute = self.extractor_class_atts(method, sub_class, current_query, parser_token_list)
                        sub_class.Attributes += attribute
                        break

            """handle answer methods"""
        elif isinstance(method, javalang.tree.MethodDeclaration) or \
                isinstance(method, javalang.tree.ConstructorDeclaration):
            if self.current_parsed != "Post":
                current_method = current_query.get_methods(method.name)
                # TODO: check methods that doesnt belong to any class
                if current_method is None:

                    if len(current_query.sub_classes) == 1:
                        current_class = current_query.sub_classes[0]
                        current_method = CodeWrapper.MethodTask(method.name, current_class)
                        current_query.sub_classes[0].add_class_methods(current_method)
                        current_query.sub_classes[0].changed_code()

                    else:
                        if current_query.query in self.unknown_methods.keys():
                            self.unknown_methods[current_query.query].append(method.name)
                        else:
                            self.unknown_methods[current_query.query] = []
                            self.unknown_methods[current_query.query].append(method.name)
                        return

                """handle methods"""
                # self.extractor_method_class(current_method, current_query, method, parser_token_list, first_map=False)
            else:
                # TODO: handle method posts
                current_class = CodeWrapper.ClassTask("unknown")
                current_method = CodeWrapper.MethodTask(method.name, current_class)
                current_query.add_methods(current_method)

            """set the method code"""
            current_method.set_code(extract_specific_code(method.position, parser_token_list, current_method,
                                                          current_query, modifiers=method.modifiers))

            self.extractor_method_class(current_method, current_query, method, parser_token_list)

            """extract method calls"""
            self.extract_method_invocation_new(method, current_query, current_method, parser_token_list)
        else:
            print('of')
            raise Exception("undifined")

    def extractor_method_class(self, current_method, current_query, method, parser_token_list, first_map=True):
        """
        extractor_method_class Function - extract everything from the method
        :param current_method:
        :param current_query:
        :param method:
        :param parser_token_list:
        :param first_map:
        :return:
        """

        """adds the method annotation"""
        if method.annotations is not None:
            for annotation in method.annotations:
                current_method.code = extract_att_code(annotation.position, parser_token_list, current_query) + \
                                      current_method.code

        """adds the method comments"""
        if method.documentation is not None:
            if isinstance(method.documentation, list):
                for documentation in method.documentation:
                    current_method.set_documentation(documentation)
                    current_method.code = current_method.documentation + '\n ' + current_method.code
            else:
                current_method.set_documentation(method.documentation)
                current_method.code = current_method.documentation + '\n ' + current_method.code

        """add method parameters for function calls"""
        if first_map:
            self.extract_method_parameters(method.parameters, current_method, current_query)

    def extractor_class_const(self, class_extract, parser_token_list, current_class, current_query):
        """
        extractor_class_const Function - extract the constructors
        :param class_extract:
        :param parser_token_list:
        :param current_class:
        :param current_query:
        :return:
        """
        if isinstance(class_extract, javalang.tree.ClassDeclaration):
            for constructor in class_extract.constructors:
                if isinstance(constructor, javalang.tree.ConstructorDeclaration):
                    self.extract_constructor(constructor, current_class, len(class_extract.constructors),
                                             parser_token_list, current_query)
        # TODO: add constructor declarations

    def extractor_class_atts(self, field, current_class, current_query, parser_token_list):
        """
        extractor_class_atts Function - extract class's attribute
        :param field:
        :param current_class:
        :param current_query:
        :param parser_token_list:
        :return attribute task mapped:
        """
        returned_attributes = []

        for declare in field.declarators:
            type_name = []
            """handle java collection with self objects"""
            data_structure = None
            if not isinstance(field.type, javalang.tree.BasicType) and field.type.arguments is not None:

                if isinstance(field.type, javalang.tree.TypeArgument):
                    raise Exception("Type declarations")
                data_structure = field.type.name
                for field_type in field.type.arguments:
                    if isinstance(field_type, javalang.tree.TypeArgument):
                        if field_type.type is not None:
                            type_name.append(field_type.type.name)
                        else:
                            type_name.append("?")

            else:
                if field.type.name not in type_name:
                    type_name.append(field.type.name)
            # TODO: attribute modifiers and documenetation

            """handle attribute code"""
            attribute_code = extract_att_code(field.position, parser_token_list, current_query, field.modifiers)
            ds_class = current_query.get_class(data_structure)
            if data_structure is not None and ds_class is None:
                ds_class = CodeWrapper.ClassTask(data_structure)
            """handle one object referenced objects"""
            if len(type_name) == 1:
                attribute_class = self.add_attributes_new(current_class, declare, current_query, type_name[0],
                                                          data_structure)
                attribute = CodeWrapper.ClassAttribute(current_class, declare.name, attribute_class,
                                                       ds_class)

            else:
                """handle more than one object referenced object (<,>)"""
                attribute_types = []
                for object_type in type_name:
                    attribute_types.append(self.add_attributes_new(current_class, declare, current_query,
                                                                   object_type, data_structure))
                    attribute = CodeWrapper.MultiTypeClassAttribute(current_class, declare.name, attribute_types,
                                                                    ds_class)

            """add attribute annotation"""
            if field.annotations is not None:
                for annotation in field.annotations:
                    attribute_code = extract_att_code(annotation.position, parser_token_list, current_query) + \
                                     attribute_code

            """add attribute documentation"""
            if not isinstance(field, javalang.tree.LocalVariableDeclaration):
                if field.documentation is not None:
                    for doc in field.documentation:
                        attribute.documentation.append(doc)
                        attribute_code += doc + '\n ' + attribute_code
            attribute.code = attribute_code

            for class_temp_att in current_class.Attributes:
                if attribute.name == class_temp_att.name:
                    current_class.Attributes.remove(class_temp_att)
                    break
            returned_attributes.append(attribute)
        return returned_attributes

    def add_attributes_new(self, current_class, declare, current_query, object_type, data_structure):
        """
        add_attributes Function - adds the class attributes
        :param data_structure:
        :param object_type:
        :param current_class:
        :param declare:
        :param current_query:
        """
        if object_type == "?":
            object_type = "extends_Object"

        if object_type == "T":
            object_type = data_structure
        elif object_type == "A" and data_structure is not None:
            object_type = data_structure

        """"checks if the current variable type is from the same class"""
        if object_type == current_class.get_class_name():
            attribute_class = current_class
        else:
            class_to_add = current_query.get_class(object_type)
            """checks if the class of the variable is already mapped"""
            if class_to_add is None:
                attribute_class = CodeWrapper.ClassTask(object_type)
            else:
                attribute_class = class_to_add
            """adds the primitive types of the class"""
        return attribute_class

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

    def super_constructor_call(self, current_method):
        """
        super_constructor_call Function - extracts the fathers constructor calls
        :param current_method:
        """
        qualifier = current_method.get_method_super_class().Extends
        method = CodeWrapper.MethodTask("Super Call", qualifier)
        qualifier.add_class_methods(method)
        if method not in current_method.calling_methods:
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
            if parameter.type.name in primitive_types or parameter.type.name in self.system_methods \
                    or parameter.type.name == 'T':
                current_class = CodeWrapper.ClassTask(parameter.type.name)
                attribute = CodeWrapper.ClassAttribute(None, parameter.name, current_class)
                method.add_method_attributes(attribute)
                continue

            current_class = current_query.get_class(parameter.type.name)
            """checks if the class is already declared"""
            if current_class is not None:
                attribute = CodeWrapper.ClassAttribute(None, parameter.name, current_class)
                method.add_method_attributes(attribute)
            else:
                new_class = CodeWrapper.ClassTask(parameter.type.name)
                attribute = CodeWrapper.ClassAttribute(None, parameter.name, new_class)
                method.add_method_attributes(attribute)

    def extract_constructor(self, constructor, current_class, number_of_constructors, parser_token_list, current_query):
        """
        extract_constructor Function - extract constructor of the class
        :param current_query:
        :param parser_token_list:
        :param number_of_constructors:
        :param constructor:
        :param current_class:
        :return:
        """
        new_constructor = current_class.get_constructor()
        if new_constructor is None:
            constructor_name = constructor.name
            new_constructor = CodeWrapper.MethodTask(constructor_name, current_class)
            if constructor.documentation is not None:
                new_constructor.documentation = constructor.documentation
        new_constructor.set_code(extract_specific_code(constructor.position, parser_token_list, constructor,
                                                       current_query, modifiers=constructor.modifiers))
        if len(current_class.Constructors) < number_of_constructors:
            current_class.add_class_methods(new_constructor)
            current_class.add_constructors(new_constructor)


# ------------------------------------------------------------------------------

class dataCollector():

    def __init__(self, path):
        """
        Data Collector Constructor - adds google credentials.
        """
        environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

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
