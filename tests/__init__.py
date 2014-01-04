# -*- coding: utf-8 -*-
import os
from attrdict import AttrDict
from unittest import main, TestCase
from metayaml import MetaYaml


class TestMetaYaml(TestCase):
    def test_myaml(self):
        my = MetaYaml("test.yaml", {"CWD": os.getcwd(), "join": os.path.join})
        for k, v in my.data.iteritems():
            print k, v
        self.assertIn("v1", my.data.main.test1)
        self.assertIn("v3", my.data.main.test1)
        self.assertEqual(my.data.main.test1[1].v2, AttrDict({'a': u'a', 'b': u'b'}))
        self.assertEqual(my.data.test_math, 900.0)
        self.assertEqual(my.data.test_math_str, "900.0 sec")

if __name__ == '__main__':
    main()
