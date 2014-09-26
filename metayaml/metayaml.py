import os
import jinja2
import yaml
from collections import Mapping, defaultdict, Iterable
from glob import glob


def omap_constructor(loader, node):
    from collections import OrderedDict
    return OrderedDict(loader.construct_pairs(node))

yaml.add_constructor(u'!omap', omap_constructor)


class MetaYamlException(Exception):
    pass


class FileNotFound(MetaYamlException):
    pass


def _to_str(value):
    if isinstance(value, unicode):
        return value
    return str(value)


class MetaYaml(object):
    eager_brackets = "${", "}"
    lazy_brackets = "$(", ")"

    def __init__(self, yaml_file, defaults=None, extend_key_word="extend",
                 extend_list=True, ignore_errors=False, ignore_not_existed_files=False):
        """
          Reads and process yaml config files

          :param yaml_file
          :type  yaml_file   str or list[str]
          :param defaults    Dictionary with default values which can be use during parsing yaml files
          :param extend_key_word  The name of section with list of included files
        """

        self._extend_key_word = extend_key_word
        self.data = defaults.copy() if defaults is not None else {}
        self.cache_template = defaultdict(lambda: {})
        self.extend_list = extend_list
        self.ignore_errors = ignore_errors
        self.ignore_not_existed_files = ignore_not_existed_files
        self.processed_files = set()

        if isinstance(yaml_file, basestring):
            yaml_file = [yaml_file]
        else:
            assert isinstance(yaml_file, Iterable)

        files = self.extend_filename(yaml_file)
        for filename in files:
            self.load(filename, self.data)

        self.substitute(self.data, self.data, [os.path.basename(files[0])], False)

    def extend_filename(self, file_list, path=None):
        files = []
        for filename in file_list:
            if not os.path.isabs(filename):
                if not path:
                    path = os.getcwdu() if isinstance(filename, unicode) else os.getcwd()

                filename = os.path.join(path, filename)

            found_files = glob(filename)
            if not self.ignore_not_existed_files and not found_files:
                raise FileNotFound("File %s not found" % filename)
            found_files.sort()
            files.extend(found_files)

        return files

    def load(self, path, data):
        if path in self.processed_files:
            return data  # file was already processed

        self.processed_files.add(path)
        basename = [os.path.basename(path)]
        file_dir = os.path.dirname(path)

        with open(path, "rb") as f:
            file_data = yaml.load(f) or {}

        data[self._extend_key_word] = file_data.get(self._extend_key_word, [])
        self.substitute(data[self._extend_key_word], data, basename, eager=True)

        extends = data[self._extend_key_word]

        if extends:
            self.substitute(data, data, basename, eager=True)
            if isinstance(extends, basestring):
                extends = [extends]

            if not isinstance(extends, Iterable):
                raise MetaYamlException("The value of %s should be list of string or string" %
                                        self._path_to_str([basename, self._extend_key_word]))

            for file_name in extends:
                if not isinstance(file_name, basestring):
                    raise MetaYamlException("The value of %s should be list of string or string" %
                                            self._path_to_str([basename, self._extend_key_word]))

            for file_name in self.extend_filename(extends, file_dir):
                try:
                    self.load(file_name, data)
                except IOError as e:
                    raise FileNotFound("Open file %s error from %s: %s" % (file_name, path, e))

        self._merge(data, file_data)
        self.substitute(data, data, basename, eager=True)

        return data

    def substitute(self, value, data, path, eager):
        path = path or []
        if isinstance(value, Mapping):
            for key, val in value.iteritems():
                new_path = path + [_to_str(key)]
                new_key = self.eval_value(key, new_path, data, eager)
                if new_key != key:
                    del value[key]
                value[new_key] = self.substitute(val, data, new_path, eager)
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

    def eval_value(self, val, path, data, eager):
        if not isinstance(val, basestring):
            return val

        brackets = self.eager_brackets if eager else self.lazy_brackets
        if brackets[0] not in val:
            return val

        # disable force string conversion
        original_to_string = jinja2.runtime.to_string
        jinja2.runtime.to_string = lambda x: x

        cache = self.cache_template[eager]
        t = cache.get(val)
        if t is None:
            try:
                t = jinja2.Template(val, variable_start_string=brackets[0], variable_end_string=brackets[1])
            except Exception, e:
                if not self.ignore_errors:
                    raise MetaYamlException("Template compiling error of key: %s, value: %s, error: %s" % (
                        self._path_to_str(path), val, e))
            cache[val] = t
        try:
            r = list(t.root_render_func(t.new_context(data)))
            if len(r) == 1:
                result = r[0]
            else:
                r = [unicode(rr) for rr in r]
                result = u"".join(r)
        except Exception as e:
            result = val
            if not self.ignore_errors:
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
                if self.extend_list:
                    a_value.extend(b_value)
                else:
                    a[key] = b_value
            else:
                a[key] = b[key]
        return a


def read(yaml_file, defaults=None, extend_key_word="extend", extend_list=True, ignore_errors=False):
    m = MetaYaml(yaml_file, defaults, extend_key_word, extend_list, ignore_errors)
    return m.data
