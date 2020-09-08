import stackoverflow_java_queries
#from googlesearch import search


class Task:

    def __init__(self):
        """
        Task Constructor - object that holds the task attribute.
        """
        self.task = None
        self.key = 0
        self.documentation = ""
        self.code = None
        self.code_changed = False
        self.imports = []
        self.imports_codes = []
        self.tags = []
        self.score = None
        self.post_id = None

    def add_id(self, post_id):
        """
        add_id Function - adds the post id
        :param post_id:
        """
        self.post_id = post_id

    def add_tags(self, tags):
        """
        add_tags Function - adds the query tags to the map
        :param tags:
        """
        self.tags = tags

    def add_score(self, score):
        """
        add_score Function - adds the score to the map
        :param score:
        """
        self.score = score

    def add_imports_code(self, _import):
        """
        add_imports_code Function - adds code imports codes to the class
        :param _import:
        """
        self.imports_codes.append(_import)

    def add_imports(self, _import):
        """
        add_imports Function - adds code imports to the class
        :param _import:
        :return:
        """
        self.imports.append(_import)

    def changed_code(self):
        """
        changed_code Function - indicates that code has been changed
        """
        self.code_changed = True

    def set_code(self, code):
        """
        set_code Function - sets the task's code
        :param code:
        """
        if self.code is not None:
            self.code_changed = True
        self.code = code

    def set_documentation(self, documentation):
        """
        set_documentation - set the documentation of the task, inherit all tasks
        :param documentation:
        """
        documentation = documentation.replace("/**", '')
        documentation = documentation.replace("*/", '')
        self.documentation += documentation

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
        self.answer_text = None
        self.sub_classes = []
        self.url = None
        self.methods = []

    def add_answer_text(self, answer_text):
        """
        add_answer_text Function - adds the answer text to the query
        :param answer_text:
        """
        self.text += answer_text

    def add_methods(self, method):
        """
        add_methods Function - creates methods list to find simple codes
        :param method:
        """
        self.methods.append(method)

    def get_methods(self, method_name):
        """
        get_methods Function - find if a method exists
        :param method_name:
        :return: list of methods
        """
        # TODO: handle two functions from same name
        return next((x for x in self.methods if x.get_method_name() == method_name), None)

    def find_url(self, url):
        # TODO: to fix function
        self.url = url

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
        self.sub_classes = []
        self.Enums = []

    def add_sub_class(self, sub_class):
        """
        add_sub_class Function - adds a sub class
        :param sub_class:
        """
        self.sub_classes.append(sub_class)

    def add_class_enums(self, enum):
        """
        add_class_enums Function - adds the class's enums declarations
        :param enum:
        """
        self.Enums.append(enum)

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

    def get_constructor(self):
        """
        get_constructor Function
        :return first constructor
        """
        if self.Constructors:
            return self.Constructors[0]
        return None

    def __eq__(self, other):
        """
        equality checker for class task
        :param other:
        :return True if classes are equal, otherwise False.
        """
        return self.class_name == other.get_class_name()


# ------------------------------------------------------------------------------
class ClassAttribute(Task):

    def __init__(self, class_task, attribute_name, att_type=None, object_type=None):
        """
        ClassAttribute constructor - builds an attribute task object
        :param class_task:
        :param attribute_name:
        """
        super().__init__()
        self.class_name = class_task
        self.name = attribute_name
        self.att_type = att_type
        self.object_type = object_type

    def get_att_obj_type(self):
        return self.object_type

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

    def get_attribute_type(self):
        return self.att_type


# ------------------------------------------------------------------------------

class MultiTypeClassAttribute(ClassAttribute):

    def __init__(self, class_task, attribute_name, att_types, object_type):
        """
        MultiTypeClassAttribute constructor - builds a multi types attribute task object
        :param class_task:
        :param attribute_name:
        :param att_types:
        :param object_type:
        """
        super().__init__(class_task, attribute_name, object_type=object_type)
        self.types = att_types


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
        self.method_token = None

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


# ------------------------------------------------------------------------------

class EnumTask(Task):

    def __init__(self, enum_name, task):
        """
        MethodTask constructor - builds the method task object
        :param method_name:
        """
        super().__init__()
        self.enum_name = enum_name
        self.super_task = task
        self.enum_consts = []

    def add_enum_const(self, const):
        """
        add_enum_const Function - adds the enum consts to the enum task
        :param const:
        """
        self.enum_consts.append(const)
