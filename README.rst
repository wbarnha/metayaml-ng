=========
Meta Yaml
=========

.. image::
  https://drone.io/bitbucket.org/atagunov/metayaml/status.png


Mata Yaml is several enhancements for yaml format that allow the following:

* include one yaml file from another
* use python expression and other fields in the file as value

Include files syntax
--------------------

To include one file or files the '**extend**' key is used. For example:

**base.yaml**::

 extend:
   - file1.yaml
   - file2.yaml
 name: base.yaml
 b: overridden_by_base
 new: new

**file1.yaml**::

  a: a
  b: b
  c: c
  name: file1.yaml

**file2.yaml**::

  a: aa
  b: bb
  d: d
  name: file2.yaml

The order and sequence of file processing is shown in the following table:


=====  =============================================  ======================================================
 Step   Action                                         Intermediate dict
=====  =============================================  ======================================================
1      Read base.yaml and extract extend key          ::

                                                       {"extend":
                                                           ["file1.yaml", "file2.yaml"] }

2      Read file1.yaml                                ::

                                                       {
                                                          "a": "a",
                                                          "b": "b",
                                                          "c": "c",
                                                          "name": "file1.yaml"
                                                       }
3      Read file2.yaml and merge/override values      ::

                                                       {
                                                          "a": "aa", # overridden
                                                          "b": "b",  # overridden
                                                          "c": "c",
                                                          "d": "d",  # added
                                                          "name": "file2.yaml" # overridden
                                                       }

4      Read rest values from base.yaml and            ::
       merge/override
                                                       {
                                                          "a": "aa",
                                                          "b": "overridden_by_base",  # overridden
                                                          "c": "c",
                                                          "d": "d",
                                                          "name": "base.yaml" # overridden
                                                          "new": "new" # added
                                                       }
=====  =============================================  ======================================================

Expression syntax
-----------------

Metayaml support any python valid expression. For this expression should be enclosed in brackets ${} or $(). The first brackets is used for eager substitute and $() for laze. I.e. expressions in $() are applied after full read file and its include files but ${} during file read.

The access to other values from expression can be done by using dictionary syntax or 'dash dictionary syntax'.

**Examples**:

**base.yaml** ::

 extend:
   - f1.yaml

 hour: ${60*60}  # just simple python expression
 ${2+2}: four  # expression can be in the key
 delay: ${hour*2}  # delay is two hour or 7200 seconds
 loggers:
   metayaml:
     name: metayaml
     level: debug
     console: false
   backend:
     name: backend
     level: ${loggers.metayaml.level}
     console: ${loggers.metayaml.console}
   ext: ${loggers.metayaml}  # copy whole dict from loggers.metayaml this key

   incorrect: ${delay} ${loggers.ext}  # In this case string representation of objects will be concatenated

**f1.yaml** ::

  run_interval: $(hour*5)  # 5 hours. But 'hour' is not defined when this file is processed.
                           # Therefore only $() brackets can be used here.

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
::

 from metayaml import read
 read(["config.yaml",
       "test.yaml"],
      {'join': os.path.join, # allows get right os specific path in yaml file
       'env': os.environ}  # allows use system environments from yaml file
     )

**config.yaml** ::

 extend:
   - ${join(env["HOME"], ".metayaml", "localconfig.yaml")} # added reading local config from $HOME
 user_name: ${env["USER"]}
 email: ${user_name + "@example.com"}
 debug: false


**test.yaml** ::

 debug: true


Order of substitution
=====================

By default the order of mapping collection (dictionary) is not defined, therefore the result of processing
of the following file is not as expected::

  A: 1
  B: ${A+1}
  AA: ${B}

The result is::

  {'A': 1, 'AA': '${A+1}', 'B': 2}


because 'AA' is substituded before 'B'.

To prevent indeterminacy the omap tag (http://yaml.org/type/omap.html) can be used::

  !omap
  A: 1
  B: ${A+1}
  AA: ${B}


Also the 'defaults' parameter **must be** OrderedDict::

  from metayaml import read
  from collections import OrderedDict

  q = read(["order.yaml"], defaults=OrderedDict())


In this case  items are processed in the definition order and the result is::

  OrderedDict([('A', 1), ('B', 2), ('AA', 2)])


License
=======
MetaYaml is released under a MIT license.
