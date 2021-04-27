#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import textwrap
import inspect
import logging


class Parameter(object):
    """
    Storage container for an "param" that can be type checked, restricted, and documented.

    The meta data within this object is designed to be immutable, the only portion of this class
    that can be changed (without demangling) is the assigned value and the default, via the
    associated setter methods: setDefault and setValue.

    The constructor will throw exceptions if the input is not correct. The other methods, including
    the setters, should not raise an exception. The two set methods return a code indicating if the
    change was successful along with the error that occurred. If successful a 0 return code
    is provided.

    !alert warning title=Use InputParameters
    This object is not designed for general use, it was designed to operated via the InputParameters
    object.

    Inputs:
        name[str]: The name of the option.
        default[]: The default value, if "vtype" is set the type must match and is not applied until
                   the validate() method ics called.
        doc[str]: A documentation string, which is used in the option dump.
        vtype[type]: The python type that this option is to be restricted.
        allow[tuple]: A tuple of allowed values, if vtype is set the types within must match.
        size[int]: Defines the size of an array, setting size will automatically set the array flag.
        array[bool]: Define the option as an "array", which if 'vtype' is set restricts the values
                     within the tuple to match types.
        required[bool]: Define if the option is required; see InputParameters.py
        private[bool]: Define if the options is private; see InputParameters.py. A parameter name
                       that starts with and underscore is assumed to be private
        verify[tuple]: Define a custom verify function and error message. The first item must
                       be a callable function with a single argument, the second item must be a str.
        mutable[bool]: Do not allow the value to change after validation.
    """
    def __init__(self,
                 name,
                 default=None,
                 doc=None,
                 vtype=None,
                 allow=None,
                 size=None,
                 array=False,
                 required=False,
                 private=None,
                 verify=None,
                 mutable=True):

        # Force vtype to be a tuple to allow multiple types to be defined
        if isinstance(vtype, type):
            vtype = (vtype, )

        self.__name = name  # option name
        self.__value = None  # current value
        self.__default = default  # default value
        self.__vtype = vtype  # option type
        self.__allow = allow  # list of allowed values
        self.__doc = doc  # documentation string
        self.__array = array  # create an array
        self.__size = size  # array size
        self.__required = required  # see validate()
        self.__verify = verify  # verification function
        self.__set_by_user = False  # flag indicating if the parameter was set after construction
        self.__mutable = mutable  # flag indicating if the parameter can change after construction
        self.__validated = False  # set by validate method, used with mutable

        if not isinstance(self.__name, str):
            msg = "The supplied 'name' argument must be a 'str', but {} was provided."
            raise TypeError(msg.format(type(self.__name)))

        # private option, must be after name to allow startswith to work without error
        self.__private = private if (private is not None) else self.__name.startswith('_')

        if (self.__doc is not None) and (not isinstance(self.__doc, str)):
            msg = "The supplied 'doc' argument must be a 'str', but {} was provided."
            raise TypeError(msg.format(type(self.__doc)))

        if (self.__vtype is not None) and (any(not isinstance(v, type) for v in self.__vtype)):
            msg = "The supplied 'vtype' argument must be a 'type', but {} was provided."
            raise TypeError(msg.format(type(self.__vtype)))

        if (self.__allow is not None) and (not isinstance(self.__allow, tuple)):
            msg = "The supplied 'allow' argument must be a 'tuple', but {} was provided."
            raise TypeError(msg.format(type(self.__allow)))

        if (self.__vtype is not None) and (self.__allow is not None):
            for value in self.__allow:
                if not isinstance(value, self.__vtype):
                    msg = "The supplied 'allow' argument must be a 'tuple' of {} items, but a {} " \
                            "item was provided."
                    raise TypeError(msg.format(self.__vtype, type(value)))

        if (self.__size is not None) and (not isinstance(self.__size, int)):
            msg = "The supplied 'size' argument must be a 'int', but {} was provided."
            raise TypeError(msg.format(type(self.__size)))

        if not isinstance(self.__required, bool):
            msg = "The supplied 'required' argument must be a 'bool', but {} was provided."
            raise TypeError(msg.format(type(self.__required)))

        if not isinstance(self.__private, bool):
            msg = "The supplied 'private' argument must be a 'bool', but {} was provided."
            raise TypeError(msg.format(type(self.__private)))

        if (self.__verify is not None) and (not isinstance(self.__verify, tuple)):
            msg = "The supplied 'verify' argument must be a 'tuple' with callable function and 'str' error message, but {} was provided."
            raise TypeError(msg.format(type(self.__verify)))

        if (self.__verify is not None) and (len(self.__verify) != 2):
            msg = "The supplied 'verify' argument must be a 'tuple' with two items a callable function and 'str' error message, but {} with {} items was provided."
            raise TypeError(msg.format(type(self.__verify), len(self.__verify)))

        if (self.__verify is not None) and (not (inspect.isfunction(self.__verify[0])
                                                 or inspect.ismethod(self.__verify[0]))):
            msg = "The first item in the 'verify' argument tuple must be a callable function with a single argument, but {} was provided"
            raise TypeError(msg.format(type(self.__verify[0])))

        if (self.__verify
                is not None) and (len(inspect.signature(self.__verify[0]).parameters) != 1):
            msg = "The first item in the 'verify' argument tuple must be a callable function with a single argument, but {} was provided that has {} arguments."
            raise TypeError(
                msg.format(type(self.__verify[0]),
                           len(inspect.signature(self.__verify[0]).parameters)))

        if (self.__verify is not None) and (not isinstance(self.__verify[1], str)):
            msg = "The second item in the 'verify' argument tuple must be a string, but {} was provided"
            raise TypeError(msg.format(type(self.__verify[1])))

        if not isinstance(self.__mutable, bool):
            msg = "The supplied 'mutable' argument must be a 'bool', but {} was provided."
            raise TypeError(msg.format(type(self.__mutable)))

        elif self.__size is not None:
            self.__array = True

    @property
    def name(self):
        """Returns the option name."""
        return self.__name

    @property
    def value(self):
        """Returns the option value."""
        retcode, err = 0, None#self.validate()
        if retcode > 0:
            raise TypeError(err)
        return self.__value

    @property
    def default(self):
        """Returns the default value for the option."""
        retcode, err = 0, None#self.validate()
        if retcode > 0:
            raise TypeError(err)
        return self.__default

    @property
    def doc(self):
        """Returns the documentation string."""
        return self.__doc

    @property
    def allow(self):
        """Returns the allowable values for the option."""
        return self.__allow

    @property
    def size(self):
        """Returns the size of the option."""
        return self.__size

    @property
    def array(self):
        """Returns the array flag of the parameter."""
        return self.__array

    @property
    def vtype(self):
        """Returns the variable type."""
        return self.__vtype

    @property
    def required(self):
        """Returns the option required state."""
        return self.__required

    @property
    def private(self):
        """Returns the option private state."""
        return self.__private

    @property
    def mutable(self):
        """Returns the option mutable state."""
        return self.__mutable

    @property
    def is_set_by_user(self):
        """Return True if the value has been set after construction."""
        retcode, err = 0, None#self.validate()
        if retcode > 0:
            raise TypeError(err)
        return self.__set_by_user

    def setRequired(self, value):
        """
        Set the required status.

        The supplied *value* should be a `bool` and this method will return a non-zero exit status
        if called after the `validate` method has been called.
        """
        if not isinstance(value, bool):
            msg = "The supplied value for `setRequired` must be a `bool`, a {} was provided."
            return 1, msg.format(self.name, type(value))

        if self.__validated:
            msg = "The Parameter has already been validated, the required state cannot be changed."
            return 1, msg.format(self.name)
        self.__required = value
        return 0, None

    def setDefault(self, val):
        """
        Set the default value for this parameter.

        The supplied *val* is the value to be assigned to the default of this parameter. The return
        values are are detailed in `setValue` method. If the value has not been assigned (i.e.,
        it is None) this method will also set the value.
        """
        #self.validate()
        retcode, error = self.__check(val)
        if retcode == 0:
            self.__default = val
            if self.__value is None:
                self.__value = self.__default
                self.__set_by_user = True
        return retcode, error

    def setValue(self, val):
        """
        Sets the value and performs a myriad of consistency checks.

        The supplied *val* is the value to be assigned to this parameter. If an error occurs
        during assignment a return code of 1 will be returned with a string of the associated
        error. If the assignment is successful a return code of 0 will be returned with None. For
        example, for a Parameter object `param` the use of this should be as follows.

        ```python
        ret, err = param.setValue(42)
        ```
        """
        retcode, error = self.__check(val)
        if retcode == 0:
            self.__value = val
            self.__set_by_user = True
        return retcode, error

    def isInstance(self, types):
        """
        Returns True if the value of the parameters is in the supplied *types*.
        """
        if self.__value is not None:
            return isinstance(self.__value, types)
        elif self.__default is not None:
            return isinstance(self.__default, types)
        return False

    def validate(self):
        """
        Validate that the Parameter is in the correct state.

        After this method is called the the "mutable" option is enforced.

        This method returns a code and error message (if any) in the same fashion as done by the
        `setValue` method.
        """
        if self.__validated:
            return 0, None

        if (self.__value is None) and (self.__default is not None):
            set_by_user = self.__set_by_user
            retcode, error = self.setDefault(self.__default)
            if not set_by_user:
                self.__set_by_user = False
            if retcode > 0:
                return retcode, error

        if self.__required and (self.value is None):
            msg = "The parameter '{}' is marked as required, but no value is assigned."
            return 1, msg.format(self.name)

        self.__validated = True
        return 0, None

    def toString(self, prefix='', level=0):
        """Create a string of Parameter information."""
        self.validate()
        from .InputParameters import InputParameters
        is_sub_option = self.isInstance(InputParameters)

        out = [self.__name]
        if prefix is not None:
            out[0] = '{} | {}{}'.format(out[0], prefix, self.__name) if prefix else out[0]

        if self.__doc is not None:
            wrapper = textwrap.TextWrapper()
            wrapper.initial_indent = ' ' * 2
            wrapper.subsequent_indent = ' ' * 2
            wrapper.width = 100
            out += [w for w in wrapper.wrap(self.__doc)]

        if is_sub_option:
            out += [self.__value.toString(prefix=self.__name + '_', level=level + 1)]

        else:
            out += ['  Value:   {}'.format(repr(self.value))]
            if self.__default is not None:
                out += ['  Default: {}'.format(repr(self.__default))]

            if self.__vtype is not None:
                out += ['  Type(s): {}'.format(tuple([t.__name__ for t in self.__vtype]))]

            if self.__allow is not None:
                wrapper = textwrap.TextWrapper()
                wrapper.initial_indent = '  Allow:   '
                wrapper.subsequent_indent = ' ' * len(wrapper.initial_indent)
                wrapper.width = 100 - len(wrapper.initial_indent)
                out += wrapper.wrap(repr(self.__allow))

        return textwrap.indent('\n'.join(out), ' ' * 4 * level)

    def __check(self, val):
        """
        Check that the supplied value is correct.

        This function is used to when setting the default and the value itself.
        """
        if self.__validated and (not self.__mutable):
            msg = "An attempt was made to change the value or default of '{}', but it is marked as immutable."
            return 1, msg.format(self.name)

        if (val is None) and (self.__required):
            msg = "'{}' was defined as required, which requires a type of {} for assignment, a value of None may not be utilized."
            return 1, msg.format(self.name, self.__vtype)

        if self.__array and not isinstance(val, tuple):
            msg = "'{}' was defined as an array, which require {} for assignment, but a {} was " \
                  "provided."
            return 1, msg.format(self.name, tuple, type(val))

        if self.__array:
            for v in val:
                if (val is not None) and (self.__vtype
                                          is not None) and not isinstance(v, self.__vtype):
                    msg = "The values within '{}' must be of type {} but {} provided."
                    return 1, msg.format(self.name, self.__vtype, type(v))

            if self.__size is not None:
                if (val is not None) and (len(val) != self.__size):
                    msg = "'{}' was defined as an array with length {} but a value with length {} " \
                          "was provided."
                    return 1, msg.format(self.name, self.__size, len(val))

        else:
            if (val is not None) and (self.__vtype
                                      is not None) and not isinstance(val, self.__vtype):
                msg = "'{}' must be of type {} but {} provided."
                return 1, msg.format(self.name, self.__vtype, type(val))

        # Check that the value is allowed
        if (val is not None) and (self.__allow is not None) and (val not in self.__allow):
            msg = "Attempting to set '{}' to a value of {} but only the following are allowed: {}"
            return 1, msg.format(self.name, val, self.__allow)

        # Call custom verify function
        if (val is not None) and (self.__verify is not None) and (not self.__verify[0](val)):
            msg = "Verify function failed with the given value of {}\n{}"
            return 1, msg.format(val, self.__verify[1])

        return 0, None

    def __str__(self):
        """Support print statement on Parameter object."""
        return self.toString()
