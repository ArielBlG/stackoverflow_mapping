import stackoverflow_java_queries
from googlesearch import search


class Task:

    def __init__(self):
        """
        Task Constructor - object that holds the task attribute.
        """
        self.task = None
        self.key = 0
        self.documentation = []

    def set_documentation(self, documentation):
        """
        set_documentation - set the documentation of the task, inherit all tasks
        :param documentation:
        """
        self.documentation = documentation

    def set_key(self, key):
        """
        set_key Function - set the map key to the task, inherit to all tasks
        :param key:
        """
        self.key = key

    def get_key(self):
        """
        get_key Function - returns the task's key
        :return:
        """
        return self.key


# ------------------------------------------------------------------------------
class CodeWrapper(Task):
    def __init__(self, query, text):
        """
        Code Wrapper Constructor - query that wraps a specific code.
        """
        super().__init__()
        self.query = query
        self.text = text
        self.sub_classes = []
        self.url = None

    def find_url(self):
        # TODO: to fix function
        for url in search(self.query, tld='com', lang='en', num=1):
            print(type(url))

    def add_class(self, task):
        """
        add_class Function - adds a class to the current query
        :param task:
        """
        self.sub_classes.append(task)

    def __eq__(self, other):
        """
        equality of two queries
        :param other:
        :return True is 2 queries are equal, otherwise False
        """
        if self.query == other.query:
            return True
        return False

    def get_queries_class(self):
        """
        get_queries_class Function - return all queries classes
        :return all queries classes
        """
        return self.sub_classes

    def get_class(self, class_to_return):
        """
        get_class Function - return a class by name
        :param class_to_return:
        :return class task object, None if doesn't exists
        """
        for curr_class in self.sub_classes:
            if curr_class.get_class_name() in stackoverflow_java_queries.primitive_types:
                continue
            else:
                if curr_class.get_class_name() == class_to_return:
                    return curr_class
        return None


# ------------------------------------------------------------------------------

class ClassTask(Task):

    def __init__(self, class_name):
        """
        ClassTask constructor - builds a task from a specific class
        :param class_name:
        """
        super().__init__()
        self.class_name = class_name
        self.Attributes = []
        self.Methods = []
        self.Implements = []
        self.Extends = None
        self.Constructors = []

    def add_implement_class(self, implement_class):
        """
        add_implenent_class Function - adds a class that the Task's classes implements
        :param implement_class:
        """
        self.Implements.append(implement_class)

    def add_extended_class(self, extended_class):
        """
        add_extended_class Function - adds an extended class from the Task's classes.
        :param extended_class:
        """
        self.Extends = extended_class

    def add_constructors(self, constructor):
        """
        add_constructors Function - adds constructor of the Task's class
        :param constructor:
        """
        self.Constructors.append(constructor)

    def add_class_methods(self, method):
        """
        add_class_methods Function - adds a method to Task's classes.
        :param method:
        """
        self.Methods.append(method)

    def add_class_attributes(self, attribute):
        """
        add_class_attributes Function - add a specific attribute to the class
        :param attribute:
        :return:
        """
        self.Attributes.append(attribute)

    def get_class_object(self):
        """
        get_class_object Function - returns the Task's task
        :return:
        """
        return self.task

    def get_class_name(self):
        """
        get_class_name Function
        :return class's name
        """
        return self.class_name

    def get_class_attributes(self):
        """
        get_class_attributes
        :return current class attributes
        """
        return self.Attributes

    def get_class_method(self, method):
        """
        get_class_method Function - recives a method name and returns a method task
        :param method:
        :return method task if recived method exists, otherwise None
        """
        return next((x for x in self.Methods if x.get_method_name() == method), None)

    def get_specific_attribute(self, attribute):
        """
        get_specific_attribute Function - returns an attribute task from received attribute name
        :param attribute:
        :return attribute task if received attribute exists, otherwise None
        """
        return next((x for x in self.Attributes if x.get_attribute_name() == attribute), None)

    def get_all_method(self):
        """
        get_all_method
        :return all current Task's class methods
        """
        return self.Methods

    def __eq__(self, other):
        """
        equality checker for class task
        :param other:
        :return True if classes are equal, otherwise False.
        """
        return self.class_name == other.get_class_name()


# ------------------------------------------------------------------------------
class ClassAttribute(Task):

    def __init__(self, class_task, attribute_name):
        """
        ClassAttribute constructor - builds an attribute task object
        :param class_task:
        :param attribute_name:
        """
        super().__init__()
        self.class_name = class_task
        self.name = attribute_name

    def get_attribute_name(self):
        """
        get_attribute_name
        :return attribute task's name:
        """
        return self.name

    def get_attribute_class(self):
        """
        get_attribute_class
        :return attributes class:
        """
        return self.class_name


# ------------------------------------------------------------------------------
class MethodTask(Task):

    def __init__(self, method_name, class_task):
        """
        MethodTask constructor - builds the method task object
        :param method_name:
        """
        super().__init__()
        self.task = class_task
        self.Attributes = []
        self.method_name = method_name
        self.calling_methods = []

    def add_method_calls(self, method):
        """
        add_method_calls - adds a method that is called from the current method task.a
        :param method:
        """
        self.calling_methods.append(method)

    def add_method_attributes(self, attribute):
        """
        add_method_attributes Function - adds an attribute to the current class - used for invocation.
        :param attribute:
        """
        self.Attributes.append(attribute)

    def get_method_name(self):
        """
        get_method_name
        :return current method's tasks name
        """
        return self.method_name

    def get_method_super_class(self):
        """
        get_method_super_class
        :return method's super class object
        """
        return self.task

    def get_calling_method(self):
        """
        get_calling_method
        :return all the methods invoked from the specific method:
        """
        return self.calling_methods

    def get_attribute(self, attribute):
        """
        get_attribute Function - returns an attribute of the method by a received attribute name.
        :return attribute task object if exists, otherwise None
        """
        return next((x for x in self.Attributes if x.get_attribute_name() == attribute), None)

    def find_method_call(self, method_called):
        """
        find_method_call Function - checks if the received method is already invoked and added.
        :param method_called:
        :return method object if the received method has been called already, otherwise None.
        """
        for calling in self.calling_methods:
            if calling.get_method_name() == method_called:
                return calling
        return None
