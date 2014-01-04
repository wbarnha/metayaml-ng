import os
import jinja2
import yaml
from attrdict import AttrDict
from collections import Mapping

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class MetaYamlException(Exception):
    pass


class FileNotFound(MetaYamlException):
    pass


class MetaYaml(object):
    def __init__(self, yaml_file, defaults=None, extend_key_word="extend"):
        self._extend_key_word = extend_key_word
        self.defaults = defaults
        self.data = AttrDict(defaults or {})

        self._current_dir = os.path.dirname(yaml_file) \
            if os.path.abspath(yaml_file) else ""
        self.load(yaml_file, self.data)
        self.substitute(self.data, self.data, "", False)

    def find_path(self, path):
        if os.path.isabs(path):
            return path

        return os.path.join(self._current_dir, path)

    def load(self, path, data):
        path = self.find_path(path)

        with open(path, "rb") as f:
            file_data = yaml.load(f, Loader=Loader)

        data[self._extend_key_word] = None
        self._merge(data, file_data)
        self.substitute(data, data, "", eager=True)
        extends = data.get(self._extend_key_word)

        if extends:
            if isinstance(extends, basestring):
                extends = [extends]
            if not isinstance(extends, list):
                raise MetaYamlException("The value of %s should be list of string or string" % self._extend_key_word)

            for file_name in extends:
                if not (isinstance(file_name, str) or isinstance(file_name, unicode)):
                    raise MetaYamlException("The value of %s should be list of string or string" %
                                            self._extend_key_word)
                try:
                    self.load(file_name, data)
                except IOError as e:
                    raise FileNotFound("Open file %s error from %s: %s" % (file_name, path, e))
        return data

    def substitute(self, value, data, path, eager):
        path = path or []
        if isinstance(value, Mapping):
            for key, val in value.iteritems():
                value[key] = self.substitute(val, data, path + [str(key)], eager)
        elif isinstance(value, list):
            for key in range(len(value)):
                value[key] = self.substitute(value[key], data, path + [str(key)], eager)
        elif isinstance(value, basestring):
            value = self.eval_value(value, path, data, eager)

        return value

    @staticmethod
    def _path_to_str(path):
        def tostr(p):
            if isinstance(p, str):
                return "." + p
            else:
                return "[%s]" % (p,)

        l = (tostr(p) for p in path)
        s = "".join(l)
        if s[0] == ".":
            s = s[1:]
        return s

    @staticmethod
    def eager_template(template):
        return jinja2.Template(template, variable_start_string="${", variable_end_string="}")

    @staticmethod
    def lazy_template(template):
        return jinja2.Template(template, variable_start_string="$(", variable_end_string=")")

    def eval_value(self, val, path, data, eager):
        path = path or None

        if eager:
            template = self.eager_template
        else:
            template = self.lazy_template

        t = template(val)
        try:
            result = t.render(**data)
        except Exception as e:
            raise MetaYamlException("Render template error of %s, %s: %s" % (self._path_to_str(path), val, e))

        for t in [int, float]:
            try:
                result = t(result)
                break
            except (ValueError, TypeError):
                pass

        # raise Exception("Can't substitute value in string: '{}' (path: {})".format(val, self._path_to_str(path)))
        return result

    def _merge(self, a, b, path=None):
        if path is None:
            path = []
        for key, b_value in b.iteritems():
            a_value = a.get(key)
            if isinstance(a_value, dict) and isinstance(b_value, dict):
                self._merge(a[key], b_value, path + [str(key)])
            elif isinstance(a_value, list) and isinstance(b_value, list):
                a_value.extend(b_value)
            else:
                a[key] = b[key]
        return a


def read(yaml_file):
    m = MetaYaml(yaml_file)
    return m.data
