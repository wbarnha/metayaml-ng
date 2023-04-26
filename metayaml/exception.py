import typing as tp


class MetaYamlException(Exception):
    pass


class FileNotFound(MetaYamlException):
    pass


class MetaYamlExceptionPath(MetaYamlException):
    @staticmethod
    def _path_to_str(path: tp.Union[tp.List[str], tp.Tuple]):
        def to_part_str(part: str):
            if isinstance(part, str):
                return f".{part}"
            else:
                return f"[{part}]"

        s = "".join(to_part_str(p) for p in path)
        if s.startswith("."):
            s = s[1:]
        return s

    def __init__(self, message, path, value):
        path = self._path_to_str(path)
        msg = f"Wrong value of '{path}' = '{value}': {message}"
        super().__init__(msg)
