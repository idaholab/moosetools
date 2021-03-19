class MooseException(Exception):
    """
    General exception.
    """
    def __init__(self, message, *args, **kwargs):
        self.__message = message.format(*args, **kwargs)
        Exception.__init__(self, self.__message)

    @property
    def message(self):
        """Return the message supplied to the constructor."""
        return self.__message
