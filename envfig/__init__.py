import inspect
import logging
import os

log = logging.getLogger(__name__)


class Property(object):
    def __init__(self, type=str, name=None, default=None):
        self._type = type
        self.name = name
        self.default = default

    @property
    def type(self):
        """
        :rtype : type
        """
        if inspect.isfunction(self._type):
            return self._type()

        return self._type

    def parse(self, path):
        # Model property
        if issubclass(self.type, Model):
            return self.type

        # Value property
        key = '.'.join([x for x in [path, self.name] if x])

        if key not in os.environ:
            return self.default

        value = os.environ[key]

        func = getattr(self, 'parse_%s' % self.type.__name__, None)

        if func is None:
            return self.type(value)

        return func(value)

    @staticmethod
    def parse_bool(value):
        value = value.lower()

        if value == 'true':
            return True

        if value == 'false':
            return False

        try:
            return bool(int(value))
        except (TypeError, ValueError), ex:
            log.warn('Invalid value for "bool" type - %s', ex)
            return None


class ModelMeta(type):
    def __init__(cls, what, bases=None, dict=None):
        super(ModelMeta, cls).__init__(what, bases, dict)

        cls.__initialized = False

        if '__key__' not in cls.__dict__:
            cls.__key__ = cls.__name__.lower()

        cls.__properties = cls.__find_properties()
        cls.__initialized = True

    def __find_properties(cls):
        result = {}

        for name, value in cls.__dict__.items():
            # Look for properties
            if value is Property or isinstance(value, Property):
                if value is Property:
                    value = Property()

                if value.name is None:
                    value.name = name

                result[name] = value

                # Remove attribute from class (so calls go through to __getattr__)
                delattr(cls, name)

        return result

    def __path(cls):
        if cls.parent and cls.parent.__path():
            return '%s.%s' % (cls.parent.__path(), cls.__key__)

        return cls.__key__

    def __getattr__(cls, name):
        if not cls.__initialized:
            return super(ModelMeta, cls).__getattribute__(name)

        prop = cls.__properties.get(name)

        if prop is None:
            return None

        return prop.parse(cls.__path())


class Model(object):
    __metaclass__ = ModelMeta
