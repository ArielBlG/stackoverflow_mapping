class TempTask:
    def __init__(self, **kw):
        """
        Task Constructor - object that holds the task attribute.
        """
        if not kw:
            dict.__init__(self)
        self.__dict__ = self

    def __getattribute__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("%s does not exist" % key)

    def __setitem__(self, key, value):
        if key not in self:
            raise AttributeError("%s does not exist" % key)

        self[key] = value
