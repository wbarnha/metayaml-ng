# -*- coding: utf-8 -*-
import os
from unittest import main, TestCase
from metayaml import read, MetaYamlException


class TestMetaYaml(TestCase):

    @staticmethod
    def _file_name(filename):
        dirname = os.path.dirname(__file__)
        return os.path.join(dirname, "test_files", filename)

    def test_myaml(self):
        d = read(self._file_name("test.yaml"), {"CWD": os.getcwd(), "join": os.path.join})
        self.assertIn("v1", d["main"]["test1"])
        self.assertNotIn("v3", d["main"]["test1"])
        self.assertEqual(d["main"]["test1"][1]["v2"], {'a': u'a', 'b': u'b'})
        self.assertEqual(d["test_math"], 900.0)
        self.assertEqual(d["test_math_str"], "900.0 sec")

        self.assertEqual(d["test2"], ['v1', {'v2': {'a': 'a', 'b': 'b'}}])
        self.assertEqual(d[10], 20)
        self.assertEqual(d["test_lazy_template"], 9)

    def test_failed_lazy_template(self):
        with self.assertRaises(MetaYamlException):
            # Render template error of test_lazy_template, $(f3*3): 'f3' is undefined
            read(self._file_name("f1.yaml"), {"join": os.path.join})

    def test_multi_file_reading(self):
        files = [self._file_name("test.yaml"), self._file_name("test_multi.yaml")]
        d = read(files, {"join": os.path.join})
        self.assertEqual(d["test_math"], 1500)
        self.assertEqual(d["f3"], 33)

    def test_multi_file_reading_match(self):
        files = [self._file_name("test.yaml"), self._file_name("test_m*.yaml")]
        d = read(files, {"join": os.path.join})
        self.assertEqual(d["test_math"], 1500)
        self.assertEqual(d["f3"], 33)

    def test_error(self):
        # Render template error of test_lazy_template, $(f3*3): 'f3' is undefined
        d = read(self._file_name("f1.yaml"), {"join": os.path.join}, ignore_errors=True)
        self.assertEqual(d["test_lazy_template"], "$(f3*3)")

    def test_dict_manipulation(self):
        d = read(self._file_name("dict_update.yaml"), {"join": os.path.join})
        self.assertNotIn("test_f1", d["main"])
        self.assertNotIn("f1", d["main"]["all"])
        self.assertNotIn("f2", d["main"]["all"])
        self.assertEqual(d["main"]["remove_all_from_here"], {8: 8})
        self.assertEqual(d["main"]["test1"], ["v3", "v4", "v5"])

    def test_disable_order_dict(self):
        d = read(self._file_name("test.yaml"), {"CWD": os.getcwd(), "join": os.path.join},
                 disable_order_dict=True)
        self.assertEqual(type(d), dict)

if __name__ == '__main__':
    main()
