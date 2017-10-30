"""
Test reactions.
"""

import gc
import sys
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event._both_tester import run_in_both, this_is_js
from flexx.util.logging import capture_log

from flexx import event

loop = event.loop
logger = event.logger


## Order

class MyObject1(event.Component):
    
    @event.reaction('!a')
    def r1(self, *events):
        print('r1 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!a', '!b')
    def r2(self, *events):
        print('r2 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!c')
    def r3(self, *events):
        pass


@run_in_both(MyObject1)
def test_reaction_order1():
    """
    r1 a a
    r2 a a
    r1 a a
    r2 a a
    """
    m = MyObject1()
    
    # since there is a reaction for c, the a events cannot join
    with loop:
        m.emit('a', {})
        m.emit('a', {})
        m.emit('c', {})
        m.emit('c', {})
        m.emit('a', {})
        m.emit('a', {})


@run_in_both(MyObject1)
def test_reaction_order2():
    """
    r1 a a
    r2 a a b b a a
    r1 a a
    r1 a
    r2 a
    """
    m = MyObject1()
    
    # for r1, the events cannot join, but they can for b
    with loop:
        m.emit('a', {})
        m.emit('a', {})
        m.emit('b', {})
        m.emit('b', {})
        m.emit('a', {})
        m.emit('a', {})
        m.emit('c', {})  # but this breaks it
        m.emit('a', {})


@run_in_both(MyObject1)
def test_reaction_order3():
    """
    r2 b a a
    r1 a a
    """
    m = MyObject1()
    
    # in all of the above r1 went first, because of its name.
    # now r2 is "triggered" first
    with loop:
        m.emit('b', {})
        m.emit('a', {})
        m.emit('a', {})


@run_in_both(MyObject1)
def test_reaction_order4():
    """
    r2 b a a
    r1 a a
    """
    m = MyObject1()
    
    # in all of the above r1 went first, because of its name.
    # now r2 is "triggered" first
    with loop:
        m.emit('b', {})
        m.emit('a', {})
        m.emit('a', {})


## Labels

class MyObject_labeled(event.Component):
    
    @event.reaction('!a')
    def r1(self, *events):
        print('r1 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!a:b')
    def r2(self, *events):
        print('r2 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!a:a')
    def r3(self, *events):
        print('r3 ' + ' '.join([ev.type for ev in events]))


@run_in_both(MyObject_labeled)
def test_reaction_labels1():
    """
    r3 a a
    r2 a a
    r1 a a
    """
    m = MyObject_labeled()
    
    # in all of the above r1 went first, because of its name.
    # now r2 is "triggered" first
    with loop:
        m.emit('a', {})
        m.emit('a', {})


## Init order

class MyObject_init(event.Component):
    
    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)
    spam = event.IntProp(settable=False)

    @event.reaction('foo', 'bar')
    def _report(self, *events):
        print('r ' + ', '.join(['%s:%i->%i' % (ev.type, ev.old_value, ev.new_value) for ev in events]))


@run_in_both(MyObject_init)
def test_reacion_init1():
    """
    0 7
    iter
    r foo:0->0, bar:7->7
    0 7
    end
    """
    # order foo bar is because of order of connection strings
    m = MyObject_init()
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init)
def test_reacion_init2():
    """
    0 7
    iter
    r foo:0->0, bar:7->7, bar:7->4, foo:0->4
    4 4
    end
    """
    # Order of first two is determined by order of connection strings
    # the next two by the property name
    m = MyObject_init(foo=4, bar=4)
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init)
def test_reacion_init3():
    """
    0 7
    iter
    r foo:0->0, bar:7->7, foo:0->2, bar:7->2
    2 2
    end
    """
    # order foo bar is because of order of connection strings
    m = MyObject_init()
    m.set_foo(2)
    m.set_bar(2)
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init)
def test_reacion_init4():
    """
    0 7
    iter
    r foo:0->0, bar:7->7, bar:7->4, foo:0->4, foo:4->2, bar:4->2
    2 2
    end
    """
    # Order of first two is determined by order of connection strings
    # the next two by the property name, the next two by order of actions.
    m = MyObject_init(foo=4, bar=4)
    m.set_foo(2)
    m.set_bar(2)
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init)
def test_reacion_init_fail1():
    """
    ? AttributeError
    ? TypeError
    """
    try:
        m = MyObject_init(blabla=1)
    except AttributeError as err:
        logger.exception(err)
    
    try:
        m = MyObject_init(spam=1)
    except TypeError as err:
        logger.exception(err)


## Reactions used not as decorators


class MyObject2(event.Component):
    
    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)


@run_in_both(MyObject2)
def test_reacion_using_react_func1():
    """
    r foo:0->0, bar:7->7, foo:0->2, bar:7->2
    r foo:0->0, bar:7->7, foo:0->3, bar:7->3
    """
    
    def foo(*events):
        print('r ' + ', '.join(['%s:%i->%i' % (ev.type, ev.old_value, ev.new_value) for ev in events]))
    
    m = MyObject2()
    m.reaction(foo, 'foo', 'bar')
    m.set_foo(2)
    m.set_bar(2)
    loop.iter()
    
    # Again, but watch order of args
    m = MyObject2()
    m.reaction('foo', 'bar', foo)
    m.set_foo(3)
    m.set_bar(3)
    loop.iter()


@run_in_both(MyObject2)
def test_reacion_using_react_func2():
    """
    r foo:0->2, bar:7->2
    r foo:0->3, bar:7->3
    """
    def foo(*events):
        print('r ' + ', '.join(['%s:%i->%i' % (ev.type, ev.old_value, ev.new_value) for ev in events]))
    
    m = MyObject2()
    loop.iter()  # this is extra
    m.reaction(foo, 'foo', 'bar')
    m.set_foo(2)
    m.set_bar(2)
    loop.iter()
    
    # Again, but watch order of args
    m = MyObject2()
    loop.iter()  # this is extra
    m.reaction('foo', 'bar', foo)
    m.set_foo(3)
    m.set_bar(3)
    loop.iter()


@run_in_both(MyObject2, js=False)  # not an issue in JS - no decorators there
def test_reacion_using_react_func3():
    """
    r foo:0->0, bar:7->7, foo:0->2, bar:7->2
    """
    
    m = MyObject2()
    
    @m.reaction('foo', 'bar')
    def foo(*events):
        print('r ' + ', '.join(['%s:%i->%i' % (ev.type, ev.old_value, ev.new_value) for ev in events]))
    
    m.set_foo(2)
    m.set_bar(2)
    loop.iter()


# not in both
def test_reaction_builtin_function():
    
    class Foo(event.Component):
        pass
    
    foo = Foo()
    foo.reaction('!bar', print)  # this should not error


## Misc


@run_in_both(MyObject1)
def test_reaction_invoking():
    """
    r1 
    r2 
    end 
    """
    m = MyObject1()
    m.r1()
    m.r2()
    loop.iter()
    print('end')


def test_reaction_exceptions1():
    m = event.Component()
    
    @m.reaction('!foo')
    def handle_foo(*events):
        1/0
    
    m.emit('foo', {})
    
    sys.last_traceback = None
    assert sys.last_traceback is None
    
    # No exception should be thrown here
    loop.iter()
    loop.iter()
    
    # But we should have prepared for PM debugging
    if sys.version_info[0] >= 3:  # not sure why
        assert sys.last_traceback
    
    # Its different for a direct call
    with raises(ZeroDivisionError):
        handle_foo()


def test_reaction_exceptions2():
    
    class Foo(event.Component):
        def __init__(self):
            super().__init__()
            self.bar = event.Component()
            self.bars = [self.bar]
    
    f = Foo()
    
    # ok
    @f.reaction('bars*.spam')
    def handle_foo(*events):
        pass
    
    # not ok
    with raises(RuntimeError) as err:
        @f.reaction('bar*.spam')
        def handle_foo(*events):
            pass
    assert 'not a tuple' in str(err)



## Meta-ish tests that are similar for property/emitter/action/reaction


@run_in_both(MyObject1)
def test_reaction_meta():
    """
    True
    r1
    [['!a', ['a:r1']]]
    [['!a', ['a:r2']], ['!b', ['b:r2']]]
    """
    m = MyObject1()
    
    print(hasattr(m.r1, 'dispose'))
    print(m.r1.get_name())
    print([list(x) for x in m.r1.get_connection_info()])  # tuple-> list
    print([list(x) for x in m.r2.get_connection_info()])


@run_in_both(MyObject1)
def test_reaction_not_settable():
    """
    fail AttributeError
    """
    
    m = MyObject1()
    
    try:
        m.r1 = 3
    except AttributeError:
        print('fail AttributeError')
    
    # We cannot prevent deletion in JS, otherwise we cannot overload


def test_reaction_python_only():
    
    m = MyObject1()
    
    # Reaction decorator needs proper callable and connection strings
    with raises(TypeError):
        event.reaction(3)
    with raises(TypeError):
        event.reaction(isinstance)
    
    # Check type of the instance attribute
    assert isinstance(m.r1, event._reaction.Reaction)
    
    # Cannot set or delete a reaction
    with raises(AttributeError):
        m.r1 = 3
    with raises(AttributeError):
        del m.r1
    
    # Repr and docs
    assert 'reaction' in repr(m.__class__.r1).lower()
    assert 'reaction' in repr(m.r1).lower()
    assert 'r1' in repr(m.r1)


run_tests_if_main()