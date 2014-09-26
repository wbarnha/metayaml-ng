# -*- coding: utf-8 -*-
import os
from attrdict import AttrDict
from unittest import main, TestCase
from metayaml import read, MetaYamlException
from collections import OrderedDict


class TestMetaYaml(TestCase):
    def test_myaml(self):
        d = read(os.path.join("test_files", "test.yaml"), {"CWD": os.getcwd(), "join": os.path.join})
        d = AttrDict(d)
        self.assertIn("v1", d.main.test1)
        self.assertIn("v3", d.main.test1)
        self.assertEqual(d.main.test1[2].v2, {'a': u'a', 'b': u'b'})
        self.assertEqual(d.test_math, 900.0)
        self.assertEqual(d.test_math_str, "900.0 sec")

        self.assertEqual(d.test2, ['v3', 'v1', {'v2': {'a': 'a', 'b': 'b'}}])
        self.assertEqual(d[10], 20)
        self.assertEqual(d.test_lazy_template, 9)

    def test_failed_lazy_template(self):
        with self.assertRaises(MetaYamlException):
            # Render template error of test_lazy_template, $(f3*3): 'f3' is undefined
            read(os.path.join("test_files", "f1.yaml"), {"join": os.path.join})

    def test_multi_file_reading(self):
        files = [os.path.join("test_files", "test.yaml"), os.path.join("test_files", "test_multi.yaml")]
        d = read(files, {"join": os.path.join})
        self.assertEqual(d["test_math"], 1500)
        self.assertEqual(d["f3"], 33)

    def test_multi_file_reading_match(self):
        files = [os.path.join("test_files", "test.yaml"), os.path.join("test_files", "test_m*.yaml")]
        d = read(files, {"join": os.path.join})
        self.assertEqual(d["test_math"], 1500)
        self.assertEqual(d["f3"], 33)

    def test_list_extend(self):
        files = [os.path.join("test_files", "list_extend.yaml")]
        d = read(files)
        self.assertEqual(d["test_list"], ["a", "b", "c", "d", "e"])

        d = read(files, extend_list=False)
        self.assertEqual(d["test_list"], ["d", "e"])

    def test_order_map(self):
        files = [os.path.join("test_files", "order.yaml")]

        d = read(files, defaults=OrderedDict())
        self.assertIsInstance(d, OrderedDict)
        self.assertEqual(d.keys(), ["extend", "A", "B", "C", "Z", "AA"])

    def test_error(self):
        # Render template error of test_lazy_template, $(f3*3): 'f3' is undefined
        d = read(os.path.join("test_files", "f1.yaml"), {"join": os.path.join}, ignore_errors=True)
        self.assertEqual(d["test_lazy_template"], "$(f3*3)")


if __name__ == '__main__':
    main()
