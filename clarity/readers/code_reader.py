"""Deterministic reader for Python source code files."""

import ast
from pathlib import Path
from dataclasses import dataclass, field


class CodeReadError(Exception):
    """Raised when code reading fails."""
    pass


@dataclass
class FunctionInfo:
    """Extracted information about a function."""
    name: str
    signature: str
    docstring: str | None
    line_start: int
    line_end: int
    is_async: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "signature": self.signature,
            "docstring": self.docstring,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "is_async": self.is_async,
        }


@dataclass
class ClassInfo:
    """Extracted information about a class."""
    name: str
    signature: str
    docstring: str | None
    line_start: int
    line_end: int
    methods: list[FunctionInfo] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "signature": self.signature,
            "docstring": self.docstring,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "methods": [m.to_dict() for m in self.methods],
            "bases": self.bases,
        }


@dataclass
class FileInfo:
    """Extracted information about a Python file."""
    path: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "imports": self.imports,
        }


def read_code(paths: list[str]) -> dict:
    """
    Read Python source files from specified paths.

    Args:
        paths: List of file or directory paths to read

    Returns:
        Dictionary with 'files' key containing list of parsed file info

    Raises:
        CodeReadError: If a path is invalid or cannot be read
        FileNotFoundError: If a path does not exist
    """
    if not paths:
        return {"files": []}

    files = []

    for path in paths:
        path_obj = Path(path)

        if not path_obj.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if path_obj.is_file():
            if path_obj.suffix == ".py":
                file_info = _read_single_file(path_obj)
                files.append(file_info.to_dict())
        elif path_obj.is_dir():
            for py_file in path_obj.rglob("*.py"):
                file_info = _read_single_file(py_file)
                files.append(file_info.to_dict())
        else:
            raise CodeReadError(f"Path is neither file nor directory: {path}")

    return {"files": files}


def _read_single_file(path: Path) -> FileInfo:
    """Read and parse a single Python file."""
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:
        raise CodeReadError(f"Failed to read file {path}: {e}")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        raise CodeReadError(f"Syntax error in {path}: {e}")

    source_lines = source.split("\n")

    file_info = FileInfo(path=str(path.resolve()))

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            file_info.functions.append(_extract_function(node, source_lines, is_async=False))
        elif isinstance(node, ast.AsyncFunctionDef):
            file_info.functions.append(_extract_function(node, source_lines, is_async=True))
        elif isinstance(node, ast.ClassDef):
            file_info.classes.append(_extract_class(node, source_lines))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            file_info.imports.extend(_extract_import(node))

    return file_info


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str], is_async: bool) -> FunctionInfo:
    """Extract function information from an AST node."""
    signature = _build_function_signature(node, is_async)
    docstring = ast.get_docstring(node)
    line_end = _get_end_line(node)

    return FunctionInfo(
        name=node.name,
        signature=signature,
        docstring=docstring,
        line_start=node.lineno,
        line_end=line_end,
        is_async=is_async,
    )


def _extract_class(node: ast.ClassDef, source_lines: list[str]) -> ClassInfo:
    """Extract class information from an AST node."""
    bases = [_node_to_string(base) for base in node.bases]
    signature = _build_class_signature(node)
    docstring = ast.get_docstring(node)
    line_end = _get_end_line(node)

    methods = []
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            methods.append(_extract_function(item, source_lines, is_async=False))
        elif isinstance(item, ast.AsyncFunctionDef):
            methods.append(_extract_function(item, source_lines, is_async=True))

    return ClassInfo(
        name=node.name,
        signature=signature,
        docstring=docstring,
        line_start=node.lineno,
        line_end=line_end,
        methods=methods,
        bases=bases,
    )


def _extract_import(node: ast.Import | ast.ImportFrom) -> list[str]:
    """Extract import statements as strings."""
    imports = []

    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.asname:
                imports.append(f"import {alias.name} as {alias.asname}")
            else:
                imports.append(f"import {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            if alias.asname:
                imports.append(f"from {module} import {alias.name} as {alias.asname}")
            else:
                imports.append(f"from {module} import {alias.name}")

    return imports


def _build_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> str:
    """Build a function signature string."""
    args = _build_arguments(node.args)
    returns = ""
    if node.returns:
        returns = f" -> {_node_to_string(node.returns)}"

    prefix = "async def" if is_async else "def"
    return f"{prefix} {node.name}({args}){returns}"


def _build_class_signature(node: ast.ClassDef) -> str:
    """Build a class signature string."""
    if node.bases:
        bases = ", ".join(_node_to_string(base) for base in node.bases)
        return f"class {node.name}({bases})"
    return f"class {node.name}"


def _build_arguments(args: ast.arguments) -> str:
    """Build argument list string from ast.arguments."""
    parts = []

    # positional-only args (before /)
    posonlyargs = getattr(args, "posonlyargs", [])
    for i, arg in enumerate(posonlyargs):
        parts.append(_format_arg(arg, args.defaults, i, len(args.args) + len(posonlyargs)))

    if posonlyargs:
        parts.append("/")

    # regular args
    num_defaults = len(args.defaults)
    num_args = len(args.args)
    for i, arg in enumerate(args.args):
        default_index = i - (num_args - num_defaults)
        if default_index >= 0:
            default = args.defaults[default_index]
            parts.append(f"{_format_arg_name(arg)}={_node_to_string(default)}")
        else:
            parts.append(_format_arg_name(arg))

    # *args
    if args.vararg:
        parts.append(f"*{_format_arg_name(args.vararg)}")
    elif args.kwonlyargs:
        parts.append("*")

    # keyword-only args
    for i, arg in enumerate(args.kwonlyargs):
        default = args.kw_defaults[i]
        if default:
            parts.append(f"{_format_arg_name(arg)}={_node_to_string(default)}")
        else:
            parts.append(_format_arg_name(arg))

    # **kwargs
    if args.kwarg:
        parts.append(f"**{_format_arg_name(args.kwarg)}")

    return ", ".join(parts)


def _format_arg(arg: ast.arg, defaults: list, index: int, total_args: int) -> str:
    """Format a single argument with potential default."""
    return _format_arg_name(arg)


def _format_arg_name(arg: ast.arg) -> str:
    """Format argument name with optional type annotation."""
    if arg.annotation:
        return f"{arg.arg}: {_node_to_string(arg.annotation)}"
    return arg.arg


def _node_to_string(node: ast.AST) -> str:
    """Convert an AST node to its string representation."""
    try:
        return ast.unparse(node)
    except Exception:
        return "<unknown>"


def _get_end_line(node: ast.AST) -> int:
    """Get the end line number of an AST node."""
    if hasattr(node, "end_lineno") and node.end_lineno is not None:
        return node.end_lineno
    return node.lineno
