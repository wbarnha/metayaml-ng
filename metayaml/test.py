# -*- coding: utf-8 -*-
import os
from attrdict import AttrDict
from unittest import main, TestCase
from metayaml import MetaYaml, MetaYamlException


class TestMetaYaml(TestCase):
    def test_myaml(self):
        my = MetaYaml(os.path.join("test_files", "test.yaml"), {"CWD": os.getcwd(), "join": os.path.join})
        d = AttrDict(my.data)
        self.assertIn("v1", d.main.test1)
        self.assertIn("v3", d.main.test1)
        self.assertEqual(d.main.test1[1].v2, AttrDict({'a': u'a', 'b': u'b'}))
        self.assertEqual(d.test_math, 900.0)
        self.assertEqual(d.test_math_str, "900.0 sec")

        self.assertEqual(d.test2, ['v1', {'v2': {'a': 'a', 'b': 'b'}}, 'v3'])
        self.assertEqual(d[10], 20)
        self.assertEqual(d.test_lazy_template, 9)

    def test_failed_lazy_template(self):
        with self.assertRaises(MetaYamlException):
            # Render template error of test_lazy_template, $(f3*3): 'f3' is undefined
            MetaYaml(os.path.join("test_files", "f1.yaml"), {"join": os.path.join})


if __name__ == '__main__':
    main()
