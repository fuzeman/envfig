import inspect
import logging
import os
import types

log = logging.getLogger(__name__)


class Property(object):
    def __init__(self, type=str, name=None, default=None, required=False):
        self._type = type
        self.name = name

        self.default = default
        self.required = required

    @property
    def type(self):
        """
        :rtype : type
        """
        if inspect.isfunction(self._type):
            return self._type()

        return self._type

    def key(self, path):
        return '.'.join([x for x in [path, self.name] if x])

    def get(self, path, defaults=True):
        if issubclass(self.type, Model):
            return self.type

        key = self.key(path)

        if defaults and key not in os.environ:
            return self.default

        return os.environ.get(key)

    def parse(self, path):
        if issubclass(self.type, Model):
            return self.type

        key = self.key(path)

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

        cls._properties = cls.__find_properties()
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

    def _path(cls):
        if cls.parent and cls.parent._path():
            return '%s.%s' % (cls.parent._path(), cls.__key__)

        return cls.__key__

    def __getattr__(cls, name):
        if not cls.__initialized:
            return super(ModelMeta, cls).__getattribute__(name)

        prop = cls._properties.get(name)

        if prop is None:
            return None

        return prop.parse(cls._path())


class Model(object):
    __metaclass__ = ModelMeta

    @classmethod
    def validate(cls):
        path = cls._path()

        for prop in cls._properties.values():
            value = prop.get(path, defaults=False)

            if inspect.isclass(value) and issubclass(value, Model):
                value.validate()
                continue

            if prop.required and value is None:
                raise ValueError('Configuration property "%s" is required' % prop.key(path))

        return True
