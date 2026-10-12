"""Component separation check (NFR-09).

Fails the build when a lower layer imports an upper one, when a component
reaches into a peer it should not know about, or when backend code imports the
frontend. This is the evidence for the NFR-09 architecture review: UI, API,
validation, evaluation and result handling are separate components that meet
only at the interfaces listed below.

Layers, top to bottom (Architecture section 3):

    api                          API Controller (+ error handler, auth middleware)
    validation / evaluation /    services, each independent of the others
    results
    metrics / storage / security  building blocks
    errors / config              shared base, imports no component

``app.main`` is the composition root that wires components together, so it may
import any of them.
"""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"

SHARED = {"errors", "config"}

# component -> the only components it may import from (besides itself).
ALLOWED_IMPORTS = {
    "api": {"validation", "evaluation", "metrics", "results", "storage", "security"} | SHARED,
    "validation": {"security"} | SHARED,
    "evaluation": {"metrics", "results", "storage", "security"} | SHARED,
    "results": SHARED,
    "metrics": SHARED,
    "storage": {"security"} | SHARED,
    "security": SHARED,
}
# Shared base modules import no component at all.
BASE_MODULES = {"errors": set(), "config": set()}
# Backend code must never import UI code.
FORBIDDEN_TOP_LEVEL = {"frontend"}


def _owner(path: Path, root: Path) -> str | None:
    """The component (or base module) a file belongs to; None for the composition root."""
    parts = path.relative_to(root).with_suffix("").parts
    if parts[0] in ALLOWED_IMPORTS or parts[0] in BASE_MODULES:
        return parts[0]
    return None if parts[0] in {"main", "__init__"} else parts[0]


def _imported_modules(path: Path, root: Path) -> list[str]:
    """Dotted names imported by a file, with relative imports resolved against ``root``'s package."""
    package = ["app", *path.relative_to(root).with_suffix("").parts[:-1]]
    modules = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)]
                prefix = ".".join(base + ([node.module] if node.module else []))
            else:
                prefix = node.module or ""
            modules.append(prefix)
            # ``from app import api`` imports the submodule ``app.api``.
            modules += [f"{prefix}.{alias.name}" for alias in node.names]
    return modules


def find_violations(root: Path) -> list[str]:
    violations = []
    for path in sorted(root.rglob("*.py")):
        owner = _owner(path, root)
        rel = path.relative_to(root).as_posix()
        if owner is not None and owner not in ALLOWED_IMPORTS and owner not in BASE_MODULES:
            violations.append(f"{rel}: package '{owner}' is not in the component map (ALLOWED_IMPORTS)")
            continue
        seen = set()
        for module in _imported_modules(path, root):
            parts = module.split(".")
            if parts[0] in FORBIDDEN_TOP_LEVEL:
                violations.append(f"{rel}: backend code imports the frontend ('{module}')")
                continue
            if parts[0] != "app" or len(parts) < 2 or owner is None:
                continue
            target = parts[1]
            if target in seen:  # ``from app.x import y`` yields both app.x and app.x.y
                continue
            seen.add(target)
            if target in {"main"}:
                violations.append(f"{rel}: imports the composition root 'app.main'")
            elif target == owner:
                continue
            elif target not in ALLOWED_IMPORTS and target not in BASE_MODULES:
                violations.append(f"{rel}: imports unknown component 'app.{target}'")
            else:
                allowed = ALLOWED_IMPORTS.get(owner, BASE_MODULES.get(owner, set()))
                if target not in allowed:
                    violations.append(f"{rel}: '{owner}' must not import '{target}' ('{module}')")
    return violations


def test_backend_respects_the_component_boundaries():
    assert find_violations(APP_DIR) == []


def test_every_architecture_component_has_a_package():
    for component in ALLOWED_IMPORTS:
        assert (APP_DIR / component / "__init__.py").exists(), f"missing package app/{component}"


# --- the checker itself: make sure it really catches violations --------------


def _write(root: Path, files: dict[str, str]) -> Path:
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return root


def test_lower_layer_importing_api_is_flagged(tmp_path):
    root = _write(
        tmp_path,
        {
            "api/__init__.py": "",
            "validation/__init__.py": "",
            "validation/checks.py": "from app.api import error_handlers\n",
        },
    )
    (violation,) = find_violations(root)
    assert "validation" in violation and "api" in violation


def test_relative_and_plain_imports_are_flagged(tmp_path):
    root = _write(
        tmp_path,
        {
            "api/__init__.py": "",
            "results/__init__.py": "",
            "results/a.py": "from ..api import routes\n",
            "metrics/__init__.py": "",
            "metrics/b.py": "import app.api.routes\n",
            "evaluation/__init__.py": "",
            "evaluation/c.py": "from app import api\n",
        },
    )
    violations = find_violations(root)
    assert len(violations) == 3


def test_peer_services_cannot_import_each_other(tmp_path):
    root = _write(
        tmp_path,
        {
            "validation/__init__.py": "",
            "evaluation/__init__.py": "",
            "validation/x.py": "from app.evaluation import runner\n",
        },
    )
    assert len(find_violations(root)) == 1


def test_backend_importing_frontend_is_flagged(tmp_path):
    root = _write(tmp_path, {"api/__init__.py": "", "api/routes.py": "import frontend.src.App\n"})
    assert find_violations(root) == ["api/routes.py: backend code imports the frontend ('frontend.src.App')"]


def test_shared_base_modules_cannot_import_components(tmp_path):
    root = _write(tmp_path, {"errors.py": "from app.results import service\n", "results/__init__.py": ""})
    assert len(find_violations(root)) == 1


def test_allowed_imports_and_composition_root_pass(tmp_path):
    root = _write(
        tmp_path,
        {
            "api/__init__.py": "",
            "api/routes.py": "from app.results import ResultService\nfrom app.errors import AppError\n",
            "evaluation/__init__.py": "",
            "evaluation/runner.py": "from app.results import ResultService\nfrom app.metrics import x\n",
            "results/__init__.py": "",
            "metrics/__init__.py": "",
            "main.py": "from app.api import routes\nfrom app.evaluation import runner\n",
        },
    )
    assert find_violations(root) == []


def test_an_unmapped_package_must_be_added_to_the_map(tmp_path):
    root = _write(tmp_path, {"newthing/__init__.py": "", "newthing/a.py": "x = 1\n"})
    assert any("not in the component map" in v for v in find_violations(root))
