import jinja2
from jinja2 import nodes
from jinja2.compiler import CodeGenerator as _CodeGenerator
from jinja2.compiler import Frame

from metayaml.exception import MetaYamlExceptionPath


class CodeGenerator(_CodeGenerator):
    def _output_child_pre(self, node: nodes.Expr, frame: Frame, finalize) -> None:
        """Output extra source code before visiting a child of an
        ``Output`` node.
        """
        if frame.eval_ctx.volatile:
            self.write("(escape if context.eval_ctx.autoescape else str)(")
        elif frame.eval_ctx.autoescape:
            self.write("escape(")
        else:
            self.write("(")  # do not str the result!!!

        if finalize.src is not None:
            self.write(finalize.src)


class Environment(jinja2.Environment):
    code_generator_class = CodeGenerator


class Template(jinja2.Template):
    environment_class = Environment


def jinja_eval_value(loader, val, path, data, eager, brackets):
    cache = loader.cache_template[eager]
    t = cache.get(val)
    undefined = jinja2.Undefined if loader.ignore_errors else jinja2.StrictUndefined
    if t is None:
        try:
            t = Template(
                val,
                variable_start_string=brackets[0],
                variable_end_string=brackets[1],
                undefined=undefined,
            )
        except Exception as e:
            if not loader.ignore_errors:
                raise MetaYamlExceptionPath(f"Template compiling error: {e}", path, val)
        cache[val] = t

    try:
        data_str_key = {str(k): v for k, v in data.items()}
        rendered = list(t.root_render_func(t.new_context(data_str_key)))
        if len(rendered) == 1:
            if isinstance(rendered[0], undefined) and not loader.ignore_errors:
                raise MetaYamlExceptionPath("Incorrect template", path, val)
            result = rendered[0]
        else:
            rendered = [str(rr) for rr in rendered]
            result = "".join(rendered)
    except MetaYamlExceptionPath:
        raise
    except Exception as e:
        result = val
        if not loader.ignore_errors:
            raise MetaYamlExceptionPath(f"Render template error: {e}", path, val)

    if isinstance(result, str):
        for t in [int, float]:
            try:
                result = t(result)
                break
            except (ValueError, TypeError):
                pass

    return result
