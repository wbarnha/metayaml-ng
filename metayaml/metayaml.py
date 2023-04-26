import os
import datetime
import typing as tp
from collections import defaultdict
from collections.abc import Iterable, MutableMapping
from copy import deepcopy
from glob import glob

import yaml

from metayaml.exception import FileNotFound, MetaYamlException, MetaYamlExceptionPath

Path = tp.Tuple


def _path(path: Path, key: tp.Union[str, int], index=False):
    if not index:
        key = str(key)

    return path + (key,)


class MetaYaml(object):
    eager_brackets = "${", "}"
    lazy_brackets = "$(", ")"

    DEL_MARKER = "${__del__}"
    DEL_ALL_MARKER = "${__del_all__}"
    EXTEND_MARKER = "${__extend__}"
    INHERIT_MARKER = "${__inherit__}"

    @staticmethod
    def cp(source: tp.Union[dict, list, tuple], *args, **kwargs):
        if isinstance(source, MutableMapping):
            result = deepcopy(source)
            for arg in args:
                result.update(arg)
            result.update(kwargs)
            return result
        elif isinstance(source, (list, tuple)):
            result = list(source)
            result.extend(args)
            return result
        raise MetaYamlException("cp method support only dict and list as source")

    def __init__(
        self,
        yaml_file: tp.Union[str, tp.List[str]],
        defaults=None,
        extend_key_word="extend",
        ignore_errors=False,
        ignore_not_existed_files=False,
    ):
        """
        Reads and process yaml config files

        :param yaml_file
        :type  yaml_file      str or list[str]
        :param defaults       Dictionary with default values which can be use during parsing yaml files
        :param extend_key_word  The name of section with list of included files
        :param ignore_errors  Do not rise exception when value can't be rendered
        :param ignore_not_existed_files Do not rise exception if the file not found
        """

        self._extend_key_word = extend_key_word
        self.data = defaults or {}
        self.data["cp"] = self.cp

        self.cache_template = defaultdict(lambda: {})
        self.ignore_errors = ignore_errors
        self.ignore_not_existed_files = ignore_not_existed_files
        self.processed_files = set()

        if isinstance(yaml_file, str):
            yaml_file = [yaml_file]
        else:
            assert isinstance(
                yaml_file, Iterable
            ), "yaml_file should be string or list of strings"

        files = self.extend_filename(yaml_file)
        for filename in files:
            self.load(filename, self.data)

        self.process_lazy(self.data, self.data, ("#",))
        self.data.pop(self._extend_key_word, None)
        if self.data["cp"] == self.cp:
            del self.data["cp"]

    def extend_filename(self, file_list: tp.List[str], path: tp.Optional[str] = None):
        files = []
        if not path:
            path = os.getcwd()

        for filename in file_list:
            if not os.path.isabs(filename):
                filename = os.path.join(path, filename)

            found_files = glob(filename)
            if not self.ignore_not_existed_files and not found_files:
                raise FileNotFound(f"File {filename} not found")
            found_files.sort()
            files.extend(found_files)

        return files

    def load(self, file_path: str, data: dict):
        if file_path in self.processed_files:
            return data  # file was already processed

        self.processed_files.add(file_path)
        key_path = (os.path.basename(file_path),)
        file_dir = os.path.dirname(file_path)

        with open(file_path, "rb") as f:
            file_data = yaml.load(f, yaml.FullLoader) or {}
            assert isinstance(file_data, dict)

        extends = file_data.pop(self._extend_key_word, [])
        if extends:
            extends = self.eval(
                extends, data, key_path + (self._extend_key_word,), eager=True
            )
            if isinstance(extends, str):
                extends = [extends]

            if not isinstance(extends, list):
                raise MetaYamlException(
                    "should be list of string or string",
                    key_path + (self._extend_key_word,),
                    extends,
                )

            for file_name in extends:
                if not isinstance(file_name, str):
                    raise MetaYamlException(
                        "should be list of string or string",
                        key_path + (self._extend_key_word,),
                        extends,
                    )

            for file_name in self.extend_filename(extends, file_dir):
                try:
                    self.load(file_name, data)
                except IOError as e:
                    raise FileNotFound(
                        f"Open file '{file_name}' error from {file_path}: {e}"
                    )

        data = self.merge_data(file_data, data, data, key_path)
        return data

    def _eval_simple_data(
        self, value, global_data: dict, path: Path, eager: bool
    ) -> tp.Tuple[bool, tp.Union[str, int, float, None]]:
        if value is None or isinstance(value, (int, float, bool)):
            return True, value
        if isinstance(value, datetime.date):
            value = str(value)
        if isinstance(value, str):
            return True, self.eval_value(value, path, global_data, eager)
        # complex type, return as is
        assert isinstance(value, (dict, list))
        return False, None

    def eval(self, value, global_data: dict, path: Path, eager: bool):
        evaluated, new_value = self._eval_simple_data(value, global_data, path, eager)
        if evaluated:
            return new_value
        return self.merge_data(value, None, global_data, path)

    def _merge_dict(self, source: dict, dest: dict, global_data: dict, path: Path):
        assert isinstance(source, dict) and isinstance(dest, dict)
        inherit = source.pop(self.INHERIT_MARKER, None)
        if inherit:
            target_path = path + (self.INHERIT_MARKER,)
            target_dict = self.eval_value(
                f"{self.eager_brackets[0]}{inherit}{self.eager_brackets[1]}",
                target_path,
                global_data,
                True,
            )
            if not isinstance(target_dict, dict):
                raise MetaYamlExceptionPath(
                    f"inherit target should be dict, but it is {type(target_dict)}",
                    target_path,
                    inherit,
                )

            target_dict = deepcopy(target_dict)
            self._merge_dict(source, target_dict, global_data, path)
            source = target_dict

        if self.DEL_ALL_MARKER in source:
            source.pop(self.DEL_ALL_MARKER)
            dest.clear()

        for key, val in source.items():
            new_path = path + (str(key),)
            if val == self.DEL_MARKER:
                dest.pop(key, None)
                continue

            new_key = self.eval_value(key, new_path, global_data, False)

            simple_data, evaluated_value = self._eval_simple_data(
                val, global_data, new_path, eager=True
            )
            if simple_data:
                dest[new_key] = evaluated_value
            else:
                dest_value = dest.get(new_key)
                if dest_value:
                    self.merge_data(val, dest_value, global_data, path)
                else:
                    new_dest = None
                    if isinstance(
                        val, dict
                    ):  # add new dict to global data before full process
                        dest[new_key] = new_dest = {}
                    dest[new_key] = self.merge_data(
                        val, new_dest, global_data, new_path
                    )
        return dest

    def merge_data(self, source, dest, global_data: dict, path: Path):
        if isinstance(source, dict):
            if dest is None:
                dest = {}
            elif not isinstance(dest, dict):
                if (
                    isinstance(dest, list)
                    and len(source) == 1
                    and self.EXTEND_MARKER in source
                ):
                    added_values = source[self.EXTEND_MARKER]
                    if not isinstance(added_values, list):
                        raise MetaYamlExceptionPath(
                            f"expected list, but have got {type(added_values)}",
                            path + (self.EXTEND_MARKER,),
                            added_values,
                        )
                    added_values = self.eval_value(
                        added_values, path, global_data, True
                    )
                    dest.extend(added_values)
                    return dest
                else:
                    raise MetaYamlExceptionPath(
                        f"dict can't be merged to {type(dest)}", path, source
                    )
            return self._merge_dict(source, dest, global_data, path)

        if isinstance(source, list):
            if dest is None:
                dest = []
            elif not isinstance(dest, list):
                raise MetaYamlExceptionPath(
                    f"list can't be merged to {type(dest)}", path, source
                )
            dest.clear()
            dest.extend(
                self.eval(item, global_data, path + (key,), True)
                for key, item in enumerate(source)
            )
            return dest

        return source

    def eval_value(self, val, path, global_data, eager):
        from metayaml.jinja_eval import jinja_eval_value

        if not isinstance(val, str):
            return val

        brackets = self.eager_brackets if eager else self.lazy_brackets
        if brackets[0] not in val:
            return val

        return jinja_eval_value(self, val, path, global_data, eager, brackets)

    def process_lazy(self, data, global_data, path: Path) -> tp.Tuple[tp.Any, bool]:
        # the first item in result is evaluated value
        # the second item is true when value was substituted
        if isinstance(data, (float, int, bool)):
            return data, False

        if isinstance(data, str):
            evaluated_value = self.eval_value(data, path, global_data, False)
            return evaluated_value, evaluated_value != data

        substituted = False
        if isinstance(data, dict):
            for key, value in list(data.items()):
                evaluated_key = self.eval_value(
                    key, _path(path, key), global_data, False
                )
                evaluated_value, changed = self.process_lazy(
                    value, global_data, _path(path, key)
                )
                substituted |= changed
                if key != evaluated_key:
                    data.pop(key)
                    substituted = True
                data[evaluated_key] = evaluated_value
            return data, substituted

        if isinstance(data, list):
            for index, value in enumerate(data):
                evaluated_value, changed = self.process_lazy(
                    value, global_data, _path(path, index, index=True)
                )
                if changed:
                    data[index] = changed
                    substituted = True
            return data, substituted
        return data, False


def read(
    yaml_file,
    defaults=None,
    extend_key_word="extend",
    ignore_errors=False,
    ignore_not_existed_files=False,
):
    """
    Reads and process yaml config files

    :param yaml_file
    :type  yaml_file      str or list[str]
    :param defaults       Dictionary with default values which can be use during parsing yaml files
    :param extend_key_word  The name of section with list of included files
    :param ignore_errors  Do not rise exception when value can't be rendered
    :param ignore_not_existed_files Do not rise exception if the file not found
    """

    m = MetaYaml(
        yaml_file, defaults, extend_key_word, ignore_errors, ignore_not_existed_files
    )
    return m.data
