"""Tiny path router: patterns like /api/auditions/<id:int>/submissions."""
import re

_CONVERTERS = {"int": r"\d+", "str": r"[^/]+", "path": r".+"}


class Router:
    def __init__(self):
        self._routes = []

    def route(self, method: str, pattern: str):
        regex, converters = self._compile(pattern)

        def register(func):
            self._routes.append((method, regex, converters, func))
            return func
        return register

    @staticmethod
    def _compile(pattern: str):
        converters, parts = {}, []
        for piece in re.split(r"(<[^>]+>)", pattern):
            match = re.fullmatch(r"<(\w+)(?::(\w+))?>", piece)
            if match:
                name, kind = match.group(1), match.group(2) or "str"
                converters[name] = int if kind == "int" else str
                parts.append(f"(?P<{name}>{_CONVERTERS[kind]})")
            else:
                parts.append(re.escape(piece))
        return re.compile("^" + "".join(parts) + "$"), converters

    def match(self, method: str, path: str):
        """Returns (func, params), or (None, allowed_methods) when only the method is wrong."""
        allowed = []
        for route_method, regex, converters, func in self._routes:
            found = regex.match(path)
            if not found:
                continue
            if route_method == method:
                return func, {k: converters[k](v) for k, v in found.groupdict().items()}
            allowed.append(route_method)
        return None, allowed
