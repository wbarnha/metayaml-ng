import os
import jinja2
import yaml
from collections import Mapping

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class MetaYamlException(Exception):
    pass


class FileNotFound(MetaYamlException):
    pass


def _to_str(value):
    if isinstance(value, unicode):
        return value
    return str(value)


class MetaYaml(object):
    def __init__(self, yaml_file, defaults=None, extend_key_word="extend"):
        self._extend_key_word = extend_key_word
        self.defaults = defaults
        #self.data = AttrDict(defaults or {})
        self.data = defaults or {}

        if isinstance(yaml_file, basestring):
            yaml_file = [yaml_file]
        else:
            assert isinstance(yaml_file, list)
            assert all(isinstance(f, basestring) for f in yaml_file)

        for filename in yaml_file:
            if os.path.abspath(filename):
                self._current_dir = os.path.dirname(filename)
                filename = os.path.basename(filename)
            else:
                self._current_dir = ""
            self.load(filename, self.data)

        self.substitute(self.data, self.data, "", False)

    def find_path(self, path):
        if os.path.isabs(path):
            return path

        return os.path.join(self._current_dir, path)

    def load(self, path, data):
        path = self.find_path(path)

        with open(path, "rb") as f:
            file_data = yaml.load(f, Loader=Loader)

        data[self._extend_key_word] = file_data.get(self._extend_key_word, [])
        self.substitute(data[self._extend_key_word], data, "", eager=True)

        extends = data[self._extend_key_word]

        if extends:
            self.substitute(data, data, "", eager=True)
            if isinstance(extends, basestring):
                extends = [extends]
            if not isinstance(extends, list):
                raise MetaYamlException("The value of %s should be list of string or string" % self._extend_key_word)

            for file_name in extends:
                if not isinstance(file_name, basestring):
                    raise MetaYamlException("The value of %s should be list of string or string" %
                                            self._extend_key_word)
                try:
                    self.load(file_name, data)
                except IOError as e:
                    raise FileNotFound("Open file %s error from %s: %s" % (file_name, path, e))

        self._merge(data, file_data)
        self.substitute(data, data, "", eager=True)

        return data

    def substitute(self, value, data, path, eager):
        path = path or []
        if isinstance(value, Mapping):
            for key, val in value.iteritems():
                new_key = self.eval_value(key, path + [_to_str(key)], data, eager)
                if new_key != key:
                    del value[key]
                value[new_key] = self.substitute(val, data, path + [_to_str(key)], eager)
        elif isinstance(value, list):
            for key in xrange(len(value)):
                value[key] = self.substitute(value[key], data, path + [_to_str(key)], eager)
        elif isinstance(value, basestring):
            value = self.eval_value(value, path, data, eager)

        return value

    @staticmethod
    def _path_to_str(path):
        def tostr(p):
            if isinstance(p, basestring):
                return "." + p
            else:
                return "[%s]" % (p,)

        l = (tostr(p) for p in path)
        s = "".join(l)
        if s.startswith("."):
            s = s[1:]
        return s

    @staticmethod
    def eager_template(template):
        return jinja2.Template(template, variable_start_string="${", variable_end_string="}", optimized=False)

    @staticmethod
    def lazy_template(template):
        return jinja2.Template(template, variable_start_string="$(", variable_end_string=")", optimized=False)

    def eval_value(self, val, path, data, eager):
        if not isinstance(val, basestring):
            return val
        if "$" not in val:
            return val

        original_to_string = jinja2.runtime.to_string
        jinja2.runtime.to_string = lambda x: x

        if eager:
            template = self.eager_template
        else:
            template = self.lazy_template

        t = template(val)
        try:
            # disable force string conversion
            r = list(t.root_render_func(t.new_context(data)))
            if len(r) == 1:
                result = r[0]
            else:
                r = [unicode(rr) for rr in r]
                result = u"".join(r)
        except Exception as e:
            raise MetaYamlException("Render template error of %s, %s: %s" % (self._path_to_str(path), val, e))
        finally:
            jinja2.runtime.to_string = original_to_string

        if isinstance(result, basestring):
            for t in [int, float]:
                try:
                    result = t(result)
                    break
                except (ValueError, TypeError):
                    pass

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


def read(yaml_file, defaults=None, extend_key_word="extend"):
    m = MetaYaml(yaml_file, defaults, extend_key_word)
    return m.data
