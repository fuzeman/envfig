import logging
logging.basicConfig(level=logging.DEBUG)

from envfig import Model, Property


class Basic(Model):
    child = Property(lambda: Child)

    test = Property
    debug = Property(bool, default=False)
    num = Property(int)


class Child(Model):
    parent = Basic

    enabled = Property(bool, default=False)


if __name__ == '__main__':
    print 'Basic.debug:', Basic.debug
    print 'Basic.test:', Basic.test
    print 'Basic.num:', Basic.num

    print 'Basic.child:', Basic.child
    print 'Basic.child.enabled:', Basic.child.enabled

    print 'Child.enabled:', Child.enabled
