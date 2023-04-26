=========
Meta Yaml
=========

Note: This is a fork of the project at https://bitbucket.org/atagunov/metayaml.

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

Metayaml supports any python valid expression. For this expression should be enclosed in brackets ${} or $().
The first brackets is used for eager substitute and $() for laze. I.e. expressions in $() are applied after
full read file and its include files but ${} during file read.

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

The substitutions are done in order of the values in the file. I.e. the following example will be failed::

  B: ${A+1}     <--- A is not defined here
  AA: ${B}
  A: 1

But the following The result is ok::

  A: 1
  B: ${A+1}
  AA: ${B}


Change merge behavior
=====================

By default it is possible to add new keys in the dict and replace the list. In some cases it is necessary to remove
keys from base file or add some values to list. For example

**base.yaml**::

  main:
      iso_3166:
        China: CN
        Honduras: HN
        Madagascar: MG

      country_codes:
        - CN
        - HN
        - MG

      country_codes_3:
        - CHN
        - HND
        - MDG

**last.yaml**::

    extend:
      - base.yaml
    main:
      iso_3166:
         China: ${__del__}  #  key 'China' will be removed from the result
         Liberia: LR  # add new key

      country_codes:
         - LR         # after merge country_codes contains only one element.

      country_codes_3:
        ${__extend__}:
          - LBR       # the result list is ["CHN", "HND", "MDG", "LBR"]


The result of the code::

    d = read("last.yaml")
    print d

    {
        "main": {
            "iso_3166": {
                "Honduras": "HN",
                "Madagascar": "MG",
                "Liberia": "LR"
            },
            "country_codes": [
                "LR"
            ],
            "country_codes_3": [
                "CHN",
                "HND",
                "MDG",
                "LBR"
            ]
        }
    }


Copy method
===========

There is method 'cp' which copy dict/list with extending::

    cron:
      daily:
        min: 0
        hour: 0

      monthly:
        min: 0
        hour: 0
        day: 1

    schedule:
      nighttask: ${cp(cron.daily, min=5)}  # min will be replaced to 5
      #  min: 5
      #  hour: 0
      daytask: ${cp(cron.daily, min=7, hour=13)} # min and hour are replaced
      #  min: 7
      #  hour: 13
      monthtask: ${cp(cron.monthly, day=2)}
      #  min: 0
      #  hour: 0
      #  day: 2

    deploy:
      subnets:
        - 1.1.1.1
        - 2.2.2.2

      base_elb:
        - 4.4.4.4
        - 5.5.5.5

      elb: ${cp(deploy.subnets, "3.3.3.3", *deploy.base_elb)}
      # - 1.1.1.1
      # - 2.2.2.2
      # - 3.3.3.3
      # - 4.4.4.4
      # - 5.5.5.5


Inherit method
==============

There are another way to copy existed dict and update some fields::

    foo:
      bar:
        baz: 1
        buz: 2
        foobar: 3
      foobar: [4, 5]

    bar:
      ${__inherit__}: foo.bar  # bar will be replaces by content of for.bar
      buz: 33

    # the result value of 'bar' will be
    #    baz: 1
    #    buz: 33
    #    foobar: 3


License
=======
MetaYaml is released under a MIT license.
