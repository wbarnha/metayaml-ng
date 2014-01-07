=========
Meta Yaml
=========

Mata Yaml is several enhancements for yaml format that allow the following:

* include one yaml file to another
* use python expression as value

Example:
--------

main.yaml ::

  a: 1
  b: 2

Installation
============
Meta Yaml is in PyPI, so it can be installed directly using::

    $ pip install metayaml

Or from BitBucket::

    $ git clone https://bitbucket.org/atagunov/metayaml
    $ cd metayaml
    $ python setup.py install

Documentation
=============

Documentation (such that it is) is available at
https://bitbucket.org/atagunov/metayaml

Usage
=====
Creation
--------
An empty AttrDict can be created with::

    a = AttrDict()

Or, you can pass an existing dict (or other type of Mapping object)::

    a = AttrDict({'foo': 'bar'})

NOTE: Unlike dict, AttrDict will not clone on creation. AttrDict's
internal dict will be the same instance as the dict passed in.

Access
------
AttrDict can be used *exactly* like a normal dict::

    > a = AttrDict()
    > a['foo'] = 'bar'
    > a['foo']
    'bar'
    > '{foo}'.format(**a)
    'bar'
    > del a['foo']
    > a.get('foo', 'default')
    'default'

AttrDict can also have it's keys manipulated as attributes to the object::

    > a = AttrDict()
    > a.foo = 'bar'
    > a.foo
    'bar'
    > del a.foo

Both methods operate on the same underlying object, so operations are
interchangeable. The only difference between the two methods is that
where dict-style access would return a dict, attribute-style access will
return an AttrDict. This allows recursive attribute-style access::

    > a = AttrDict({'foo': {'bar': 'baz'}})
    > a.foo.bar
    'baz'
    > a['foo'].bar
    AttributeError: 'dict' object has no attribute 'bar'

There are some valid keys that cannot be accessed as attributes. To be
accessed as an attribute, a key must:

 * be a string

 * start with an alphabetic character

 * be comprised solely of alphanumeric characters and underscores

 * not map to an existing attribute name (e.g., get, items)

To access these attributes while retaining an AttrDict wrapper (or to
dynamically access any key as an attribute)::

    > a = AttrDict({'_foo': {'bar': 'baz'}})
    > a('_foo').bar
    'baz'

Merging
-------
AttrDicts can be merged with eachother or other dict objects using the
+ operator. For conflicting keys, the right dict's value will be
preferred, but in the case of two dictionary values, they will be
recursively merged::

    > a = {'foo': 'bar', 'alpha': {'beta': 'a', 'a': 'a'}}
    > b = {'lorem': 'ipsum', 'alpha': {'bravo': 'b', 'a': 'b'}}
    > AttrDict(a) + b
    {'foo': 'bar', 'lorem': 'ipsum', 'alpha': {'beta': 'a', 'bravo': 'b', 'a': 'b'}}

NOTE: AttrDict's add is not idempotent, a + b != b + a::

    > a = {'foo': 'bar', 'alpha': {'beta': 'b', 'a': 0}}
    > b = {'lorem': 'ipsum', 'alpha': {'bravo': 'b', 'a': 1}}
    > b + AttrDict(a)
    {'foo': 'bar', 'lorem':             'ipsum', 'alpha': {'beta': 'a', 'bravo': 'b', 'a': }}

License
=======
AttrDict is released under a MIT license.
