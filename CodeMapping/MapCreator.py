import json


def handle_quality(quality_dict, key):
    """
    handle_quality Function - adds quality bar to the query
    :param quality_dict:
    :param key:
    """
    quality_dict["category"] = "Quality"
    quality_dict["text"] = "Quality"
    quality_dict["fill"] = "#ffffff"
    quality_dict["stroke"] = "#000000"
    quality_dict["strokeWidth"] = 1
    quality_dict["key"] = key
    quality_dict["refs"] = []
    quality_dict["ctsx"] = []
    quality_dict["comment"] = "null"


def handle_task(mapped_dict, name, key, comments=None, post=None, code=None):
    """
    handle_task Function - creates the pattern of a task
    :param mapped_dict:
    :param name:
    :param key:
    :param comments:
    :param post:
    """
    mapped_dict["category"] = "Task"
    mapped_dict["text"] = name
    mapped_dict["fill"] = "#ffffff"
    mapped_dict["stroke"] = "#000000"
    mapped_dict["strokeWidth"] = 1
    mapped_dict["key"] = key
    mapped_dict["refs"] = []
    mapped_dict["ctsx"] = []
    mapped_dict["comment"] = comments
    mapped_dict["post"] = post
    mapped_dict["code"] = code


def handle_arrows(mapped_arrows_dict, first_key, second_key, category, text):
    """
    handle_arrows Function - creates the pattern of the arrows
    :param mapped_arrows_dict:
    :param first_key:
    :param second_key:
    :param category:
    :param text:
    :return:
    """
    mapped_arrows_dict["category"] = category
    mapped_arrows_dict["text"] = text
    mapped_arrows_dict["routing"] = {"yb": "Normal", "oE": 1}
    mapped_arrows_dict["from"] = first_key
    mapped_arrows_dict["to"] = second_key
    mapped_arrows_dict["refs"] = []
    mapped_arrows_dict["ctsx"] = []
    mapped_arrows_dict["comment"] = "null"


class MapCreator:

    def __init__(self, mapped_code):
        """
        MapCreator constructor - initiate a map object
        :param mapped_code:
        """
        self.mapped_code = mapped_code
        self.map_list = []
        self.current_mapped_classes = []
        self.current_mapped_methods = []

    def create_dictionary(self, query=None):
        """
        create_dictionary Function - creates the map dictionary to turn into json.
        :return the map of all dictionaries
        """
        if query is not None:
            curr_query = query

            for task in self.mapped_code[curr_query]:
                full_task_dict = {"class": "go.GraphLinksModel", "nodeDataArray": [], "linkDataArray": []}
                key = -1
                self.current_query = task
                """ add the query task"""
                key, full_task_dict, query_key = self.create_query_task(task, full_task_dict, key)

                """ extract the class  """
                key, full_task_dict = self.create_class_task(task, full_task_dict, key, query_key)

                """ extract the implemented class  """
                key, ull_task_dict = self.add_implemented_task(task, full_task_dict, key)

                """extract the extended class """
                key, full_task_dict = self.add_extended_task(task, full_task_dict, key)

                """ extract the class's methods  """
                key, full_task_dict = self.create_method_tasks(task, full_task_dict, key)

                """extract the class's attributes"""
                # key, full_task_dict = self.create_attribute_tasks(code, full_task_dict, key)

                """extract the calling methods"""
                key, full_task_dict = self.add_calling_methods(task, full_task_dict, key)

                self.map_list.append(full_task_dict)

            return self.map_list
        for curr_query in self.mapped_code.keys():
            full_task_dict = {"class": "go.GraphLinksModel", "nodeDataArray": [], "linkDataArray": []}
            key = -1
            for task in self.mapped_code[curr_query]:
                """ add the query task"""
                key, full_task_dict, query_key = self.create_query_task(task, full_task_dict, key)

                """ extract the class  """
                key, full_task_dict = self.create_class_task(task, full_task_dict, key, query_key)

                """ extract the implemented class  """
                key, ull_task_dict = self.add_implemented_task(task, full_task_dict, key)

                """extract the extended class """
                key, full_task_dict = self.add_extended_task(task, full_task_dict, key)

                """ extract the class's methods  """
                key, full_task_dict = self.create_method_tasks(task, full_task_dict, key)

                """extract the class's attributes"""
                # key, full_task_dict = self.create_attribute_tasks(code, full_task_dict, key)

                """extract the calling methods"""
                key, full_task_dict = self.add_calling_methods(task, full_task_dict, key)

                self.map_list.append(full_task_dict)

        return self.map_list

    def create_query_task(self, code, full_task_dict, key):
        """
        create_query_task Function - creates the query task
        :param code:
        :param full_task_dict:
        :param key:
        :return:
                :param key:
                :param full_task_dict:
                :param query_key:
        """
        mapped_task_dict = {}
        code.set_key(key)
        query_key = key
        handle_task(mapped_task_dict, code.query, key, comments=None, post=code.text, code=code.code)
        key = key - 1
        """append the task to the map"""
        full_task_dict["nodeDataArray"].append(mapped_task_dict)
        return key, full_task_dict, query_key

    def create_class_task(self, code, full_task_dict, key, query_key):
        """
        create_class_task Function - create the class task
        :param query_key:
        :param key:
        :param code:
        :param full_task_dict:
        :return:
                :param key:
                :param full_task_dict:
        """
        for sub_class in code.sub_classes:
            mapped_task_dict = {}
            mapped_arrows_dict = {}
            sub_class.set_key(key)
            handle_task(mapped_task_dict, sub_class.class_name, key, comments=sub_class.documentation,
                        code=sub_class.code)
            key = key - 1
            """append the class to the map"""
            full_task_dict["nodeDataArray"].append(mapped_task_dict)
            """append connections to the map"""
            handle_arrows(mapped_arrows_dict, query_key, sub_class.get_key(), "ConsistsOf", "consists of")
            full_task_dict["linkDataArray"].append(mapped_arrows_dict)
            self.current_mapped_classes.append(sub_class)
        return key, full_task_dict

    def add_implemented_task(self, code, full_task_dict, key):
        """
        add_implemented_task Function - create the implemented class of the main class task.
        :param code:
        :param full_task_dict:
        :return:
                :param key:
                :param full_task_dict:
        """
        for sub_class in code.sub_classes:
            for implement_class in sub_class.Implements:
                mapped_arrows_dict = {}
                """connect the tasks of the implemented class and the main class"""
                handle_arrows(mapped_arrows_dict, sub_class.get_key(), implement_class.get_key(), "AchievedBy",
                              "achieved by")
                full_task_dict["linkDataArray"].append(mapped_arrows_dict)
                key = key - 1
                self.current_mapped_classes.append(implement_class)
        return key, full_task_dict

    def add_extended_task(self, code, full_task_dict, key):
        """

        :param code:
        :param full_task_dict:
        :return:
        """
        for sub_class in code.sub_classes:
            if sub_class.Extends is not None:
                mapped_arrows_dict = {}
                handle_arrows(mapped_arrows_dict, sub_class.get_key(), sub_class.Extends.get_key(), "ExtendedBy",
                              "extended by")
                full_task_dict["linkDataArray"].append(mapped_arrows_dict)
                key = key - 1
                self.current_mapped_classes.append(sub_class.Extends)
        return key, full_task_dict

    def create_method_tasks(self, code, full_task_dict, key):
        """
        create_method_tasks Function - create the class's method tasks
        :param code:
        :param full_task_dict:
        :return:
                :param key:
                :param full_task_dict:
        """
        for sub_class in code.sub_classes:
            for method in sub_class.Methods:
                mapped_arrows_dict = {}
                mapped_task_dict = {}
                handle_task(mapped_task_dict, method.method_name, key, comments=method.documentation, code=method.code)
                method.set_key(key)
                """adds the method to the map"""
                full_task_dict["nodeDataArray"].append(mapped_task_dict)
                handle_arrows(mapped_arrows_dict, sub_class.get_key(), key, "ConsistsOf", "consists of")
                """connects the arrows from method to super class"""
                full_task_dict["linkDataArray"].append(mapped_arrows_dict)
                key = key - 1
                self.current_mapped_methods.append(method)
        return key, full_task_dict

    def create_attribute_tasks(self, code, full_task_dict, key):
        """

        :param code:
        :param full_task_dict:
        :return:
        """
        for sub_class in code.sub_classes:
            for attribute in sub_class.Attributes:
                mapped_arrows_dict = {}
                mapped_task_dict = {}
                handle_task(mapped_task_dict, attribute.name, key)
                attribute.set_key(key)
                full_task_dict["nodeDataArray"].append(mapped_task_dict)
                handle_arrows(mapped_arrows_dict, sub_class.get_key(), key, "AchievedBy", "achieved by")
                full_task_dict["linkDataArray"].append(mapped_arrows_dict)
                key = key - 1
        return key, full_task_dict

    def get_method_task(self, method_name):
        for method in self.current_mapped_methods:
            if method.method_name == method_name:
                return method
        return None

    def add_calling_methods(self, code, full_task_dict, key):
        """
        add_calling_methods Function - adds the called methods to the map
        :param code:
        :param full_task_dict:
        :return:
                :param key:
                :param full_task_dict:
        """
        for sub_class in code.sub_classes:
            for method in sub_class.Methods:
                for calling_method in method.calling_methods:
                    mapped_arrows_dict = {}
                    mapped_task_dict = {}
                    "avoid system calls"
                    linked_method = self.get_method_task(calling_method.method_name)
                    if linked_method is None:
                        continue
                    """checks if the called method is already mapped"""
                    if calling_method.get_key() == 0:
                        handle_task(mapped_task_dict, method.method_name, key)
                        full_task_dict["nodeDataArray"].append(mapped_task_dict)
                        current_key = key
                        key = key - 1
                    else:
                        current_key = linked_method.get_key()
                    """connect the arrows from a specific method to its called methods"""
                    handle_arrows(mapped_arrows_dict, method.get_key(), current_key, "ConsistsOf",
                                  "consists of")
                    full_task_dict["linkDataArray"].append(mapped_arrows_dict)
        return key, full_task_dict
