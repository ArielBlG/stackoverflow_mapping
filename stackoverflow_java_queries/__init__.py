import os
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
from py4j.java_gateway import JavaGateway, launch_gateway, GatewayParameters


class Errors(Enum):
    FAILED_PARSING = 1
    PYTHON_EXCEPTION = 2


Position = namedtuple('Position', ['line', 'column'])
PATH = os.path.dirname(__file__)

Body_Dict = namedtuple('Body_Dict', ['text', 'code', 'tags'])
Post_Dict = namedtuple('post_dict', ['text', 'code', 'score'])

primitive_types = ['Boolean', 'boolean', 'char', 'byte', 'short', 'int', 'long', 'float', 'double', 'String', 'string',
                   'System', 'System.out', 'Scanner', 'Log']


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
        body_mapping = {}
        answer_mapping = {}
        # index = 0

        """splits the data frame into body and answers"""
        body_df = self.data[["title", "body", "tags"]]
        answer_df = self.data[["title", "answers_body", "score"]]
        body_df = body_df.drop_duplicates(subset=['title'])


        # code_dict = pd.DataFrame(columns=['title', 'text', 'code'])

        for index, df_row in body_df.iterrows():
            text, code = self.extract_code_text_to_dict(df_row['body'])
            """extract the tags"""
            tags = df_row['tags'].split('|')
            body_dict = Body_Dict(text, code, tags)
            body_mapping[df_row['title']] = body_dict
            answer_mapping[df_row['title']] = []

        for index, df_row in answer_df.iterrows():
            text, code = self.extract_code_text_to_dict(df_row['answers_body'])
            body_dict = Post_Dict(text, code, df_row['score'])
            answer_mapping[df_row['title']].append(body_dict)

        return body_mapping, answer_mapping

    def extract_code_text_to_dict(self, post):
        text = ""
        code = []
        for curr_text in re.findall(r"<p>(.*?)</p>", post, flags=re.DOTALL):
            text += curr_text
        # code_dict['text'][index] = text
        row = re.sub('<p>.*?</p>', '', post)
        for curr_code in re.findall(r"<code>(.*?)</code>", row, flags=re.DOTALL):
            curr_code = curr_code.replace('&gt;', '>')
            curr_code = curr_code.replace('&lt;', '<')
            curr_code = curr_code.replace('&amp;&amp;', '&&')
            curr_code = curr_code.replace('&amp;', '&')
            curr_code = curr_code.replace('&quot;', '"')
            curr_code = curr_code.replace('...', '/** ...*/')
            code.append(curr_code)
        # title = df_row['title'] + answer_post
        # df2 = pd.DataFrame([[title, text, code]], columns=['title', 'text', 'code'])
        # code_dict = pd.concat([df2, code_dict])
        return text, code

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
                curr_code = curr_code.replace('&amp;&amp;', '&&')
                curr_code = curr_code.replace('&amp;', '&')
                curr_code = curr_code.replace('&quot;', '"')
                code.append(curr_code)
            ##TODO: if code == null
            title = df_row['title'] + answer_post
            df2 = pd.DataFrame([[title, text, code]], columns=['title', 'text', 'code'])
            code_dict = pd.concat([df2, code_dict])
            index += 1

        return code_dict


# ------------------------------------------------------------------------------

def extract_specific_code(position, parser_token_list, obj, current_query, modifiers=None):
    """
    extract_specific_code Function - extract code from parse tree
    :param position:
    :param parser_token_list:
    :param modifiers:
    :return:
    """
    current_query.changed_code()
    start_index = 0
    for token in parser_token_list:
        if token.position == position:
            break
        start_index += 1

    if modifiers is not None:
        while start_index > 0 and position[0] == parser_token_list[start_index].position[0]:
            start_index -= 1
        if start_index != 0:
            start_index += 1
        col_position = parser_token_list[start_index].position[1]
    else:
        col_position = position[1]

    end_index = start_index + 1
    for index in range(start_index + 1, len(parser_token_list)):
        if parser_token_list[index].position[1] == col_position and parser_token_list[index].value == '}':
            if isinstance(parser_token_list[index], javalang.tokenizer.Separator):
                break
        end_index += 1
    code = javalang.tokenizer.reformat_tokens(parser_token_list[start_index:end_index + 1])
    if isinstance(obj, CodeWrapper.MethodTask):
        obj.method_token = parser_token_list[start_index:end_index + 1]
    return code


def create_collected_code(query):
    new_code = []
    new_tokens = []
    changed_methods = []
    non_changed_classes = []
    for sub_class in query.sub_classes:
        if sub_class.code_changed:
            new_code.append(sub_class.code)
        else:
            # non_changed_classes.append(sub_class)
            class_name = sub_class.get_class_name()
            non_changed_classes.append(sub_class)
    for modified_class in non_changed_classes:
        if modified_class.code is None:
            continue
        new_class_code = ""
        # qualifier_name = expression.qualifier.split('.')[0]
        new_class_code += modified_class.code.split('{')[0] + "{\n"
        # tokens = new_class_code.split(new_class_code[0])
        # indent = len(tokens[0])
        whitespace = list(takewhile(str.isspace, new_class_code))
        "".join(whitespace)
        indent = len(whitespace) + 4
        for class_enum in modified_class.Enums:
            new_class_code += (' ' * indent) + class_enum.code
        for class_atts in modified_class.Attributes:
            new_class_code += (' ' * indent) + class_atts.code
        for class_method in modified_class.Methods:
            if class_method.code is not None:
                new_indenet = '\n ' + ' ' * indent
                method_code = class_method.code.replace('\n', new_indenet)
                new_class_code += (' ' * indent) + method_code + '\n '
        new_class_code += (' ' * (indent - 4)) + '}' + '\n'

        modified_class.code = new_class_code


def extract_att_code(position, parser_token_list, current_query, modifiers=None):
    current_query.changed_code()

    start_index = 0
    for token in parser_token_list:
        if token.position == position:
            break
        start_index += 1

    if modifiers is not None:
        while start_index > 0 and position[0] == parser_token_list[start_index].position[0]:
            start_index -= 1
        start_index += 1
        col_position = parser_token_list[start_index].position[1]
    else:
        col_position = position[1]

    end_index = start_index + 1
    for index in range(start_index + 1, len(parser_token_list)):
        if parser_token_list[index].position[0] != position[0]:
            break
        end_index += 1
    code = javalang.tokenizer.reformat_tokens(parser_token_list[start_index:end_index])
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
        # fin = open("/Users/ariel-pc/Desktop/Package/java_classes_names.txt", "rt")
        fin = open(os.path.join(os.path.dirname(__file__), 'java_classes_names.txt'), "rt")
        for line in fin:
            line = line.replace('\n', '')
            self.system_methods.append(line)
        fin.close()
        fin = open(os.path.join(os.path.dirname(__file__), 'java_util_names.txt'), "rt")
        for line in fin:
            line = line.replace('\n', '')
            self.java_util_method.append(line)
        fin.close()

    def parse_code_new(self):

        """handle posts"""
        for title, body_dict in self.body_mapping.items():
            class_tokens = []
            current_query = CodeWrapper.CodeWrapper(title, body_dict[0])
            self.mapped_code[title] = []
            # current_query.find_url() # TODO: fix the url
            current_query.set_code(body_dict[1])
            current_query.add_tags(body_dict[2])
            self.current_parsed = "Post"
            for code in body_dict[1]:
                # parser_token_list = self.code_parser_class(code, current_query)
                # class_tokens.append(parser_token_list)
                self.code_parser_class(code, current_query)
            """handle answers"""
            for answer_body_dict in self.answer_mapping[title]:
                self.parsing_error = None
                copy_query = copy.deepcopy(current_query)
                copy_query.add_answer_text(answer_body_dict[0])
                copy_query.add_score(answer_body_dict[2])
                copy_query.code_changed = False
                # copy_query = current_query
                self.current_parsed = "Answer"
                for answer_code in answer_body_dict[1]:
                    self.code_parser_class(answer_code, copy_query)
                if self.parsing_error is not Errors.FAILED_PARSING and copy_query.code_changed and copy_query.code:
                    # TODO: check imports
                    create_collected_code(copy_query)
                    self.mapped_code[copy_query.query].append(copy_query)

            """check if mapped code succeed"""
            if not self.mapped_code[copy_query.query]:
                self.mapped_code.pop(copy_query.query)

            # create_collected_code(copy_query)

            # TODO:check if worked
            # self.mapped_code.remove(current_query)
            """get the working code"""

        return self.mapped_code

    def code_parser_class(self, code, current_query):
        try:
            tokens = javalang.tokenizer.tokenize(code)
            parser = javalang.parser.Parser(tokens)
            parser_token_list = parser.tokens.list
            tree = javalang.parse.parse(code)
            if tree.imports:
                self.handle_imports(tree.imports, current_query)
            for class_extract in tree.types:
                self.extractor_class(class_extract, current_query, parser_token_list)

        # TODO: FIX EXCEPTIONS
        except:
            self.code_parser_method(code, current_query)

            # if self.parsing_error == Errors.FAILED_PARSING:
            #     print(self.java_error_detector.check_syntax(code))
            # else:
            #     return

    def extractor_class(self, class_extract, current_query, parser_token_list):
        """adds the calls name and create task object"""
        current_class = current_query.get_class(class_extract.name)
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
        self.extractor_class_const(class_extract, parser_token_list, current_class, current_query)

        """adds the class attributes to the task"""
        for field in class_extract.fields:
            # self.extractor_class_atts(field, current_class, current_query, parser_token_list)
            attribute = self.extractor_class_atts(field, current_class, current_query,
                                                  parser_token_list)  # TODO: new_method_class_change
            current_class.add_class_attributes(attribute)  # TODO: new_method_class_change

        """adds the class methods to the task"""
        for method in class_extract.methods:
            current_method = current_class.get_class_method(method.name)
            if current_method is None:
                current_method = CodeWrapper.MethodTask(method.name, current_class)
                current_class.add_class_methods(current_method)
                if self.current_parsed == "Post":
                    current_query.add_methods(current_method)
            current_method.set_code(extract_specific_code(method.position, parser_token_list, current_method,
                                                          current_query, modifiers=method.modifiers))

            self.extractor_method_class(current_method, current_query, method, parser_token_list)

        """handle method function calls"""
        if class_extract is not None:
            for method in class_extract.methods:
                current_method = current_class.get_class_method(method.name)
                # self.extract_method_invocation(method.children, current_query, current_method)
                self.extract_method_invocation_new(method, current_query, current_method, parser_token_list)
        else:
            # self.extract_method_invocation(method.children, current_query, current_method)
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
        if method.body is None:
            return
        for method_body in method.body:
            """handle declarations"""
            if isinstance(method_body, javalang.tree.Declaration):
                # raise Exception("not implemented variable declarator")
                self.handle_method_declarations(method_body, method, current_query, current_method, parser_token_list)

            """handle statments"""
            if isinstance(method_body, javalang.tree.Statement):
                # raise Exception("not implemented statement handler")
                self.handle_method_statements(method_body, method, current_query, current_method, parser_token_list)

            """handle expression"""
            if isinstance(method_body, javalang.tree.Expression):
                # raise Exception("not implemented expression handler")
                self.handle_method_expressions(method_body, method, current_query, current_method, parser_token_list)

    def handle_unkown_node(self, node, method, current_query, current_method, parser_token_list):
        """handle declarations"""
        if isinstance(node, javalang.tree.Declaration):
            # raise Exception("not implemented variable declarator")
            self.handle_method_declarations(node, method, current_query, current_method, parser_token_list)

        """handle statments"""
        if isinstance(node, javalang.tree.Statement):
            # raise Exception("not implemented statement handler")
            self.handle_method_statements(node, method, current_query, current_method, parser_token_list)

        """handle expression"""
        if isinstance(node, javalang.tree.Expression):
            # raise Exception("not implemented expression handler")
            self.handle_method_expressions(node, method, current_query, current_method, parser_token_list)

    def handle_method_expressions(self, expression, method, current_query, current_method, parser_token_list):
        if expression is None:
            return
        # Assignment
        if isinstance(expression, javalang.tree.Assignment):
            self.handle_method_assignment(expression, method, current_query, current_method, parser_token_list)
            # raise Exception("not implemeneted assignment expression")
        # MethodReference
        elif isinstance(expression, javalang.tree.MethodReference):
            expression.method.qualifier = expression.expression.member

            # def handle_self_method_calls(self, expression, method, current_query, current_method):
            self.handle_self_method_calls(expression.method, method, current_query, current_method)
        # Invocation
        elif isinstance(expression, javalang.tree.Invocation):
            self.handle_method_invokes(expression, method, current_query, current_method)
            # raise Exception("not implemented invocations expression")
        # Cast
        elif isinstance(expression, javalang.tree.Cast):
            # raise Exception("not implemented invocations expression")
            self.handle_method_expressions(expression.expression, method, current_query, current_method,
                                           parser_token_list)
        #MemberReference
        elif isinstance(expression, javalang.tree.MemberReference):
            # TODO: check if ok
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        #This
        elif isinstance(expression, javalang.tree.This):
            # TODO: check if ok
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)
        #Literal
        elif isinstance(expression, javalang.tree.Literal):
            # TODO: check if ok
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)
        #BinaryOperation
        elif isinstance(expression, javalang.tree.BinaryOperation):
            self.handle_method_expressions(expression.operandl, method, current_query, current_method, parser_token_list)
            self.handle_method_expressions(expression.operandr, method, current_query, current_method, parser_token_list)
        #TernaryExpression
        elif isinstance(expression, javalang.tree.TernaryExpression):
            self.handle_method_expressions(expression.condition, method, current_query, current_method, parser_token_list)
            self.handle_method_expressions(expression.if_false, method, current_query, current_method, parser_token_list)
            self.handle_method_expressions(expression.if_true, method, current_query, current_method, parser_token_list)
        #ClassCreator
        elif isinstance(expression, javalang.tree.ClassCreator):
            self.handle_method_class_calls(expression, method, current_query, current_method, parser_token_list)
        #ArrayCreator
        elif isinstance(expression, javalang.tree.ArrayCreator):
            #TODO : to complete array creator
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)
        #ClassReference
        elif isinstance(expression, javalang.tree.ClassReference):
            #TODO : to complete class reference
            self.handle_method_expressions(None, method, current_query, current_method, parser_token_list)

        #LambdaExpression
        elif isinstance(expression, javalang.tree.LambdaExpression):
            if isinstance(expression.body, list):
                for body in expression.body:
                    self.handle_unkown_node(body, method, current_query, current_method, parser_token_list)
            else:
                self.handle_unkown_node(expression.body, method, current_query, current_method, parser_token_list)

        else:
            print("stop")
            raise Exception("not implemented expression")

    def handle_method_class_calls(self, expression, method, current_query, current_method, parser_token_list):
        if expression.type.name in self.system_methods:
            return
        for sub_class in current_query.sub_classes:
            if sub_class.class_name == expression.type.name:
                sub_class_const = sub_class.get_class_method(expression.type.name)
                if sub_class_const is None:
                    sub_class_const = sub_class.get_constructor()
                if sub_class_const is None:
                    sub_class_const = CodeWrapper.MethodTask(sub_class, sub_class)
                current_method.add_method_calls(sub_class_const)
                return
        #TODO: BE-CAREFULL
        sub_class = CodeWrapper.ClassTask(expression.type.name)
        sub_class_const = CodeWrapper.MethodTask(sub_class, sub_class)
        current_method.add_method_calls(sub_class_const)
        # raise Exception("not implemented super class calls")

    def handle_method_assignment(self,expression, method, current_query, current_method, parser_token_list):
        for exp_children in expression.children:
            if isinstance(exp_children, javalang.tree.Expression):
                self.handle_method_expressions(exp_children, method, current_query, current_method, parser_token_list)
            #TODO : check relevent else

    def handle_method_invokes(self, expression, method, current_query, current_method):
        # SuperConstructorInvocation
        if isinstance(expression, javalang.tree.SuperConstructorInvocation):
            raise Exception("not implemented SuperConstructorInvocation")
        # SuperMethodInvocation
        elif isinstance(expression, javalang.tree.SuperMethodInvocation):
            self.handle_super_method_calls(expression, method, current_query, current_method)
            # raise Exception("not implemented SuperMethodInvocation")
        # MethodInvocation
        elif isinstance(expression, javalang.tree.MethodInvocation):
            self.handle_self_method_calls(expression, method, current_query, current_method)
            # raise Exception("not implemented MethodInvocation")
        # ClassReference
        elif isinstance(expression, javalang.tree.ClassReference):
            raise Exception("not implemented ClassReference")
        else:
            raise Exception("not implemented invoke")

    def handle_self_method_calls(self, expression, method, current_query, current_method):
        if expression.qualifier is not None:
            qualifier_list = expression.qualifier.split('.')
            call_qualifier = qualifier_list[0]
            if call_qualifier in self.system_methods or call_qualifier  in primitive_types:
                return
            method_att = current_method.get_attribute(call_qualifier)
            if method_att is not None:
                method_att_class = method_att.get_att_obj_type()
                if method_att_class is None:
                    method_att_class = method_att.get_attribute_type()
                if method_att_class is None:
                    raise Exception("problem with declare")
                else:
                    called_method = method_att_class.get_class_method(expression.member)
                    if called_method is None:
                        called_method = CodeWrapper.MethodTask(expression.member, method_att_class)
                    current_method.add_method_calls(called_method)
                    return #TODO: change to normal if
            else:
                for sub_class in current_query.sub_classes:
                    called_method = sub_class.get_class_method(expression.member)
                    if called_method is not None:
                        current_method.add_method_calls(called_method)
                        return #TODO: change to normal if
        #TODO: be carefull!
            called_method = CodeWrapper.MethodTask(expression.member, call_qualifier)
            current_method.add_method_calls(called_method)
        else:
            raise Exception("handle no qualifier method invokes")

    def handle_super_method_calls(self, expression, method, current_query, current_method):
        """

        :param expression:
        :param method:
        :param current_query:
        :param current_method:
        :return:
        """
        current_class = current_method.get_method_super_class()
        if expression.qualifier is None:
            if current_class.Extends is not None:
                extends_class = current_class.Extends
                super_method = extends_class.get_constructor()
                if super_method is None:
                    super_method_task = CodeWrapper.MethodTask(extends_class, extends_class)
                current_method.add_method_calls(super_method_task)
            elif current_class.Implements is not None:
                if len(current_class.Implements) == 1:
                    impl_class = current_class.Implements[0]
                    super_method = impl_class.get_constructor()
                    if super_method is None:
                        super_method = CodeWrapper.MethodTask(impl_class, impl_class)
                    current_method.add_method_calls(super_method)
                else:
                    #TODO: HANDLE UNKOWN SUPER INVOKES
                    return
        else:
            for class_impl in current_class.Implements:
                if class_impl.class_name == expression.qualifier:
                    impl_class = class_impl
                    break
            super_method = class_impl.get_constructor()
            if super_method is None:
                super_method = CodeWrapper.MethodTask(impl_class, impl_class)
            current_method.add_method_calls(super_method)

    def handle_method_statements(self, statement, method, current_query, current_method, parser_token_list):
        if statement is None:
            return
        # IfStatement
        if isinstance(statement, javalang.tree.IfStatement):
            # raise Exception("not implmeneted if statement")
            self.handle_method_statements(statement.then_statement, method, current_query, current_method,
                                          parser_token_list)
            self.handle_method_statements(statement.else_statement, method, current_query, current_method,
                                          parser_token_list)
        # WhileStatement
        elif isinstance(statement, javalang.tree.WhileStatement):
            self.handle_method_statements(statement.body, method, current_query, current_method, parser_token_list)
            # raise Exception("not implmeneted while statement")
        # DoStatement
        elif isinstance(statement, javalang.tree.DoStatement):
            self.handle_method_statements(statement.body, method, current_query, current_method, parser_token_list)
            self.handle_unkown_node(statement.condition, method, current_query, current_method, parser_token_list)
            # raise Exception("not implmeneted do statement")
        # ReturnStatement
        elif isinstance(statement, javalang.tree.ReturnStatement):
            self.handle_method_expressions(statement.expression, method, current_query, current_method, parser_token_list)
            # raise Exception("not implmeneted return statement")
        #StatementExpression
        elif isinstance(statement, javalang.tree.StatementExpression):
            self.handle_method_expressions(statement.expression, method, current_query, current_method, parser_token_list)
        #BlockStatement
        elif isinstance(statement, javalang.tree.BlockStatement):
            for block_statement in statement.statements:
                self.handle_unkown_node(block_statement, method, current_query, current_method, parser_token_list)
        # ForStatement
        elif isinstance(statement, javalang.tree.ForStatement):
            #TODO: didn't handle enhance for statement
            self.handle_method_statements(statement.body, method, current_query, current_method, parser_token_list)
        # TryStatement
        elif isinstance(statement, javalang.tree.TryStatement):
            if statement.block is not None:
                for try_block in statement.block:
                    self.handle_unkown_node(try_block, method, current_query, current_method, parser_token_list)

            if statement.catches is not None:
                for try_catch in statement.catches:
                    self.handle_unkown_node(try_catch, method, current_query, current_method, parser_token_list)

            if statement.finally_block is not None:
                for try_finally in statement.finally_block:
                    self.handle_unkown_node(try_finally, method, current_query, current_method, parser_token_list)
        #CatchClause
        elif isinstance(statement, javalang.tree.CatchClause):
            for catch_block in statement.block:
                self.handle_unkown_node(catch_block, method, current_query, current_method, parser_token_list)
        #ThrowStatement
        elif isinstance(statement, javalang.tree.ThrowStatement):
            self.handle_method_expressions(statement.expression, method, current_query, current_method, parser_token_list)
        # SwitchStatement
        elif isinstance(statement, javalang.tree.SwitchStatement):
            for switch_cases in statement.cases:
                self.handle_method_statements(switch_cases, method, current_query, current_method, parser_token_list)
            self.handle_method_expressions(statement.expression, method, current_query, current_method, parser_token_list )
        #SwitchStatementCase
        elif isinstance(statement, javalang.tree.SwitchStatementCase):
            for statements in statement.statements:
                self.handle_unkown_node(statements, method, current_query, current_method, parser_token_list)
        # BreakStatement, ContinueStatement
        elif isinstance(statement, javalang.tree.BreakStatement) or \
                isinstance(statement, javalang.tree.ContinueStatement):
            return
        #TODO: FINISH TEST STATEMENTS
        # AssertStatement

    def handle_method_declarations(self, declarations, method, current_query, current_method, parser_token_list):

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
        # LocalVariableDeclaration
        # elif isinstance(declarations, javalang.tree.LocalVariableDeclaration):
        #     raise Exception("not implemented local variable decelerator")
        # VariableDeclarator
        elif isinstance(declarations, javalang.tree.VariableDeclarator):
            raise Exception("not implemented local variable decelerator")
        else:
            raise Exception("undifiend declarators")

    def handle_variable_decelerator(self, declarations, method, current_query, current_method, parser_token_list):
        #      extractor_class_atts
        current_class = current_method.get_method_super_class()
        if isinstance(declarations, javalang.tree.LocalVariableDeclaration):
            # attribute = self.extractor_class_atts(declarations, current_class,)
            attribute = self.extractor_class_atts(declarations, current_class, current_query, parser_token_list)
            current_method.add_method_attributes(attribute)
        else:
            raise Exception("missiong variable decelerator")

    def handle_imports(self, code_imports, current_query):

        for curr_import in code_imports:
            import_value = ""
            import_value = curr_import.path.split('.')
            if import_value[-1] != "*":
                current_query.add_imports(import_value[-1])

    def get_field_declaration(self, field, current_query, parser_token_list):
        """

        :param field:
        :param current_query:
        :param parser_token_list:
        :return:
        """
        for sub_class in current_query.sub_classes:
            for declare in field.declarators:
                attribute = sub_class.get_specific_attribute(declare.name)
                if attribute is not None:
                    attribute_code = extract_att_code(field.position, parser_token_list, current_query, field.modifiers)
                    attribute.code = attribute_code
                    return
            for method in sub_class.Methods:
                for declare in field.declarators:
                    attribute = method.get_attribute(declare.name)
                    if attribute is not None:
                        attribute_code = extract_att_code(field.position, parser_token_list,
                                                          current_query, field.modifiers)
                        attribute.code = attribute_code
                        return

        """map unknown attributes"""
        if current_query.query in self.unknown_attributes.keys():
            self.unknown_attributes[current_query.query].append(field.declarators[0].name)
        else:
            self.unknown_attributes[current_query.query] = []
            self.unknown_attributes[current_query.query].append(field.declarators[0].name)
        return
        # raise Exception("new attribute to unkown place")

    def handle_field_parser(self, declares, current_query, parser_token_list):

        new_attributes = []
        for declare in declares.declarators:

            for sub_class in current_query.sub_classes:
                attribute = sub_class.get_specific_attribute(declare.name)
                if attribute is not None:
                    new_attributes.append(attribute)
                    break

                for method in sub_class.Methods:
                    attribute = method.get_attribute(declare.name)
                    if attribute is not None:
                        new_attributes.append(attribute)
                        break

    def code_parser_method(self, code, current_query):
        """

        :param code:
        :param current_query:
        :return:
        """
        try:
            tokens = javalang.tokenizer.tokenize(code)
            parser = javalang.parser.Parser(tokens)
            method = parser.parse_member_declaration()
            parser_token_list = parser.tokens.list
        # TODO: CHECK EXCPETIONS
        except:
            self.parsing_error = Errors.FAILED_PARSING
            return

        if isinstance(method, javalang.tree.ClassDeclaration):
            self.extractor_class(method, current_query, parser_token_list)
            return

        if isinstance(method, javalang.tree.FieldDeclaration):
            # self.extractor_class(method, current_query, parser_token_list)
            # self.handle_field_parser(method, current_query, parser_token_list)
            # TODO: handle method attributes changes
            for declare in method.declarators:
                for sub_class in current_query.sub_classes:
                    attribute = sub_class.get_specific_attribute(declare.name)
                    if attribute is not None:
                        # self.add_attributes_new(sub_class, declare, current_query, )
                        # self.extractor_class_atts(method, sub_class, current_query, parser_token_list) #TODO: new_method_class_change
                        attribute = self.extractor_class_atts(method, sub_class, current_query,
                                                              parser_token_list)  # TODO: new_method_class_change
                        sub_class.add_class_attributes(attribute)  # TODO: new_method_class_change

                        break
            return

            """handle answer methods"""
        elif self.current_parsed != "Posts":
            current_method = current_query.get_methods(method.name)
            # TODO: check methods that doesnt belong to any class
            if current_method is None:
                if current_query.query in self.unknown_methods.keys():
                    self.unknown_methods[current_query.query].append(method.name)
                else:
                    self.unknown_methods[current_query.query] = []
                    self.unknown_methods[current_query.query].append(method.name)
                return

            self.extractor_method_class(current_method, current_query, method, parser_token_list, first_map=False)

            # raise Exception("unknown method")
            # current_class = current_class = CodeWrapper.ClassTask("unknown")
            # current_method = CodeWrapper.MethodTask(method.name, current_class)
            # self.extractor_method_class(current_method, current_query, method)
        else:
            # TODO:check what is happening here
            raise Exception("post is a method")
            current_class = current_class = CodeWrapper.ClassTask("unknown")
            current_method = CodeWrapper.MethodTask(method.name, current_class)
            self.extractor_method_class(current_method, current_query, method, parser_token_list)

        current_method.set_code(extract_specific_code(method.position, parser_token_list, current_method,
                                                      current_query, modifiers=method.modifiers))

        # self.extract_method_invocation(method.children, current_query, current_method)
        self.extract_method_invocation_new(method, current_query, current_method, parser_token_list)

    def extractor_method_class(self, current_method, current_query, method, parser_token_list, first_map=True):
        """adds the method annotation"""
        if method.annotations is not None:
            for annotation in method.annotations:
                current_method.code = extract_att_code(annotation.position, parser_token_list, current_query) +\
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
        if isinstance(class_extract, javalang.tree.ClassDeclaration):
            for constructor in class_extract.constructors:
                if isinstance(constructor, javalang.tree.ConstructorDeclaration):
                    self.extract_constructor(constructor, current_class, len(class_extract.constructors),
                                             parser_token_list, current_query)
        # TODO: add constructor declarations

    def extractor_class_atts(self, field, current_class, current_query, parser_token_list):
        """

        :param field:
        :param current_class:
        :param current_query:
        :param parser_token_list:
        :return:
        """
        # if isinstance(field, javalang.tree.FieldDeclaration):
        type_name = []
        for declare in field.declarators:
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
            """check if this att already appended"""
            if declare.name not in current_class.get_class_attributes():
                """handle attribute code"""
                attribute_code = extract_att_code(field.position, parser_token_list, current_query, field.modifiers)
                ds_class = None
                if data_structure is not None:
                    ds_class = CodeWrapper.ClassTask(data_structure)
                """handle one object referenced objects"""
                if len(type_name) == 1:
                    attribute_class = self.add_attributes_new(current_class, declare, current_query, type_name[0])
                    attribute = CodeWrapper.ClassAttribute(current_class, declare.name, attribute_class,
                                                           ds_class)
                    # current_class.add_class_attributes(attribute) #TODO: new_method_class_change

                else:
                    """handle more than one object referenced object (<,>)"""
                    attribute_types = []
                    for object_type in type_name:
                        attribute_types.append(self.add_attributes_new(current_class, declare, current_query,
                                                                       object_type))
                    attribute = CodeWrapper.MultiTypeClassAttribute(current_class, declare.name, attribute_types,
                                                                    ds_class)
                    # current_class.add_class_attributes(attribute) #TODO: new_method_class_change

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

                return attribute  # TODO: new_method_class_change

    def add_attributes_new(self, current_class, declare, current_query, object_type):
        """
        add_attributes Function - adds the class attributes
        :param object_type:
        :param current_class:
        :param declare:
        :param current_query:
        """
        if object_type == "?":
            object_type = "extends_Object"

        """"checks if the current variable type is from the same class"""
        if object_type == current_class.get_class_name():
            # attribute_class = CodeWrapper.ClassAttribute(current_class, declare.name)
            attribute_class = current_class
        else:
            # TODO: check the fields objects type
            class_to_add = current_query.get_class(object_type)
            """checks if the class of the variable is already mapped"""
            if class_to_add is None:
                attribute_class = CodeWrapper.ClassTask(object_type)
                # if object_type not in primitive_types and object_type not in self.system_methods and object_type != "T":
                #     current_query.add_class(attribute_class)
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

    def extract_method_invocation(self, children_list, current_query, current_method):
        """
        extract_method_invocation Function - extract the method's function calls recursively
        :param children_list:
        :param method_list:
        :param current_query:
        :param current_method:
        """
        for expression in children_list:

            # if isinstance(expression, javalang.tree.Cast):
            #     if isinstance(expression.expression, javalang.tree.SuperMethodInvocation):
            #         #TODO: CHECK FUTURE CASTING OPTIONS
            #         expression.expression.qualifier = expression.type.name
            #         self.connect_methods_to_class(current_method, current_query, expression.expression)

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
                    if isinstance(expression, javalang.tree.VariableDeclaration):
                        # TODO:check if it ruins stuff, its checking iteration
                        att_type = expression.type.name
                        self.extract_method_locals(current_query, att_type, expression.declarators, current_method)

                    elif expression is not None and (
                            isinstance(expression, javalang.tree.Statement) or
                            isinstance(expression, javalang.tree.Declaration) or
                            isinstance(expression, javalang.tree.Expression) or
                            isinstance(expression, javalang.tree.EnhancedForControl)):

                        self.extract_method_invocation(expression.children, current_query, current_method)

    def super_constructor_call(self, current_method):
        """
        super_constructor_call Function - extracts the fathers constructor calls
        :param current_method:
        """
        qualifier = current_method.get_method_super_class().Extends
        method = CodeWrapper.MethodTask("Super Call", qualifier)
        qualifier.add_class_methods(method)
        current_method.add_method_calls(method)

    # TODO: check function
    def extract_method_parameters(self, parameters, method, current_query):
        """
        extract_method_parameters Function - extract method parameters for the function calls
        :param parameters:
        :param method:
        :param current_query:
        """
        for parameter in parameters:
            """skips primitive parameters"""
            # TODO: check if necessary
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
                # TODO: check the fields objects type
                new_class = CodeWrapper.ClassTask(parameter.type.name)
                # current_query.add_class(new_class)
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
        new_constructor.set_code(extract_specific_code(constructor.position, parser_token_list, constructor,
                                                       current_query, modifiers=constructor.modifiers))
        if len(current_class.Constructors) < number_of_constructors:
            current_class.add_class_methods(new_constructor)
            current_class.add_constructors(new_constructor)

    # TODO: check function
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
        """adds primitive local declares"""
        # if declare_type in primitive_types or declare_type in self.system_methods:
        #     return
        for declare in declarator:
            """check if variable already declared"""
            check_declared = current_method.get_attribute(declare.name)
            if check_declared is not None:
                continue
            """handle constructor calls"""
            if isinstance(declare.initializer, javalang.tree.ClassCreator):
                class_to_add = current_query.get_class(declare_type)
                if declare_type in self.system_methods or declare_type in primitive_types:
                    new_class = CodeWrapper.ClassTask(declare_type)
                    attribute = CodeWrapper.ClassAttribute(None, declare.name, new_class)
                else:
                    self.constructor_calls(class_to_add, current_method, current_query, declare, declare_type)
                    continue
                """checks if the local is from the same class of method"""
            elif declare_type == current_class.get_class_name():
                attribute = CodeWrapper.ClassAttribute(None, declare.name, current_class)

            elif declare_type not in primitive_types and declare_type not in self.system_methods:
                class_to_add = current_query.get_class(declare_type)
                """checks if the variable type class is already declared"""
                if class_to_add is None:
                    new_class = CodeWrapper.ClassTask(declare_type)
                    # current_query.add_class(new_class)
                    attribute = CodeWrapper.ClassAttribute(None, declare.name, new_class)
                    # new_class.add_class_attributes(attribute)
                else:
                    attribute = CodeWrapper.ClassAttribute(None, declare.name, class_to_add)
            else:
                new_class = CodeWrapper.ClassTask(declare_type)
                attribute = CodeWrapper.ClassAttribute(None, declare.name, new_class)

            current_method.add_method_attributes(attribute)

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

        method = None
        qualifier = None
        # TODO: check if working ok
        if expression.qualifier is not None and '.' in expression.qualifier:
            qualifier_name = expression.qualifier.split('.')[0]
            # TODO: check fields from this
        else:
            qualifier_name = expression.qualifier
        method_name = expression.member

        """checks if the method is already mapped"""
        if current_method.find_method_call(method_name) is not None:
            return

        """handle super calls"""
        if isinstance(expression, javalang.tree.SuperMethodInvocation):
            # if current_method.get_method_super_class().Extends is None
            if qualifier_name is None:
                if current_method.get_method_super_class().Extends is None:
                    if len(current_method.get_method_super_class().Implements) == 0:
                        if current_query.query in self.unknown_methods.keys():
                            self.unknown_methods[current_query.query].append(current_method)
                        else:
                            self.unknown_methods[current_query.query] = []
                            self.unknown_methods[current_query.query].append(current_method)
                        return
                    else:
                        qualifier = current_method.get_method_super_class().Implements[0]
                else:
                    qualifier = current_method.get_method_super_class().Extends
                # if qualifier is None:  # TODO: check if not working
                #    raise Exception("Problem with super class")
                #    return
            else:
                qualifier = current_query.get_class(qualifier_name)

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
                self.handle_uknown_calls(current_method, current_query, method_name)
                return
            """update method call"""
            current_method.add_method_calls(method)

        else:
            current_attribute = current_method.get_attribute(qualifier_name)
            """checks if the variable is declared from method and extract the class task"""
            if current_attribute is not None:
                qualifier = current_attribute.get_attribute_type()
                method = qualifier.get_class_method(method_name)
                if method is None:
                    # TODO: check if deleted more than should
                    """check if the method invoke is a system method"""
                    if qualifier.get_class_name() in self.system_methods or qualifier.class_name in primitive_types:
                        """save system methods calling in case"""
                        # method = CodeWrapper.MethodTask(method_name, qualifier)
                        # qualifier.add_class_methods(method)
                        return
                    else:
                        method = CodeWrapper.MethodTask(method_name, qualifier)
                        qualifier.add_class_methods(method)
                """update method call"""
                current_method.add_method_calls(method)

            elif qualifier_name not in self.system_methods:
                """check if its a class variable"""
                qualifier_att = current_method.get_method_super_class().get_specific_attribute(qualifier_name)
                if qualifier_att is not None:
                    qualifier_class = qualifier_att.get_att_obj_type()
                    if qualifier_class is None:
                        qualifier_class = qualifier_att.get_attribute_type()
                        if qualifier_class is None:
                            raise Exception("i dont know")
                    if qualifier_class.class_name not in self.system_methods and \
                            qualifier_class.class_name not in current_query.imports:
                        method = qualifier_class.get_class_method(method_name)
                        if method is None:
                            # print("error")
                            return
                        else:
                            current_method.add_method_calls(method)
                else:
                    """handle other classes calls"""
                    method = current_query.get_methods(method_name)
                    if method is not None:
                        current_method.add_method_calls(method)
                    else:
                        # TODO: BE CAREFULL
                        if qualifier_name not in current_query.imports:
                            new_class = CodeWrapper.ClassTask(qualifier_name)
                            method = CodeWrapper.MethodTask(method_name, new_class)
                            current_method.add_method_calls(method)
                            # print("test")

                # if qualifier_name not in self.system_methods and qualifier_name not in primitive_types:

                #     self.handle_system_calls(current_method, current_query, method_name, qualifier_class_attribute,
                #                              qualifier_name)

    def handle_uknown_calls(self, current_method, current_query, method_name):
        """
        handle_uknown_calls Function - handle unknown classes calls
        :param current_method:
        :param current_query:
        :param method_name:
        """
        qualifier = CodeWrapper.ClassTask("unkown")
        current_query.add_class(qualifier)
        method = CodeWrapper.MethodTask(method_name, qualifier)
        qualifier.add_class_methods(method)
        current_method.add_method_calls(method)

    def constructor_calls(self, class_to_add, current_method, current_query, declare, declare_type):
        """
        constructor_calls Function - extract initiation calls
        :param class_to_add:
        :param current_method:
        :param current_query:
        :param declare:
        :param declare_type:
        """
        new_class = None
        if class_to_add is None:
            # TODO: check if wrong assignment
            new_class = CodeWrapper.ClassTask(declare_type)
            current_query.add_class(new_class)

            new_method = CodeWrapper.MethodTask(declare_type, new_class)
            new_class.add_constructors(new_method)
            new_class.add_class_methods(new_method)

            current_method.add_method_calls(new_method)

            attribute = CodeWrapper.ClassAttribute(new_class, declare.name, att_type=new_class)
            current_method.add_method_attributes(attribute)

        else:
            new_method = class_to_add.get_constructor()
            if new_method is None:
                new_method = CodeWrapper.MethodTask(declare_type, class_to_add)
                class_to_add.add_constructors(new_method)
                class_to_add.add_class_methods(new_method)

                current_method.add_method_calls(new_method)

                attribute = CodeWrapper.ClassAttribute(class_to_add, declare.name, class_to_add)
                current_method.add_method_attributes(attribute)
            else:
                current_method.add_method_calls(new_method)

                attribute = CodeWrapper.ClassAttribute(class_to_add, declare.name, class_to_add)
                current_method.add_method_attributes(attribute)


# ------------------------------------------------------------------------------

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
