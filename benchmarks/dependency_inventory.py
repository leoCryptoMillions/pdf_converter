"""Inventory the installed dependency closure; no commercial compliance verdict."""
from collections import deque
from importlib import metadata
import hashlib
import json
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOTS = {"prototype": ["pdfplumber", "pydantic", "openpyxl", "python-docx", "reportlab"],
         "benchmark": ["pypdfium2", "pytesseract", "camelot-py", "psutil"]}


def inventory(roots: dict[str, list[str]] = ROOTS) -> dict:
    queue = deque(name for names in roots.values() for name in names)
    components = {}
    notices = Path(".generated/licenses/notices")
    notices.mkdir(parents=True, exist_ok=True)
    while queue:
        name = canonicalize_name(queue.popleft())
        if name in components:
            continue
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            components[name] = {"name": name, "missing": True}
            continue
        licenses = [value.split(" :: ")[-1] for value in dist.metadata.get_all("Classifier", []) if value.startswith("License ::")]
        component = {"name": name, "version": dist.version, "purl": f"pkg:pypi/{name}@{dist.version}",
                     "license_expression": dist.metadata.get("License-Expression"),
                     "license_metadata": dist.metadata.get("License"), "license_classifiers": licenses,
                     "declared_dependencies": [], "notice_files": []}
        for raw in dist.requires or []:
            requirement = Requirement(raw)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            dependency = canonicalize_name(requirement.name)
            try:
                installed = metadata.version(dependency)
                matches = installed in requirement.specifier
            except metadata.PackageNotFoundError:
                installed, matches = None, False
            component["declared_dependencies"].append({"name": dependency, "specifier": str(requirement.specifier),
                                                      "installed_version": installed, "version_satisfies": matches})
            queue.append(dependency)
        for file in dist.files or []:
            basename = Path(str(file)).name.lower()
            if "license" not in basename and "copying" not in basename and "notice" not in basename:
                continue
            path = Path(dist.locate_file(file))
            if not path.is_file():
                continue
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            destination = notices / name / (digest[:12] + "_" + path.name)
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes(data)
            component["notice_files"].append({"distribution_file": str(file).replace("\\", "/"),
                                             "sha256": digest, "size_bytes": len(data),
                                             "copied_to": str(destination).replace("\\", "/")})
        components[name] = component
    return {"scope": "installed Python dependency closure, current platform and no optional extras; native binaries/models require separate review",
            "roots": roots, "components": list(components.values()),
            "compatibility_findings": [{"component": c["name"], "dependency": d["name"],
                                         "required": d["specifier"], "installed": d["installed_version"]}
                                        for c in components.values() for d in c.get("declared_dependencies", [])
                                        if not d["version_satisfies"]],
            "legal_review_status": "PENDING; metadata and copied notices are evidence, not compliance certification"}


if __name__ == "__main__":
    report = inventory()
    destination = Path(".generated/licenses/inventory.json")
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"components": len(report["components"]), "compatibility_findings": report["compatibility_findings"],
                      "notice_files": sum(len(c.get("notice_files", [])) for c in report["components"]),
                      "legal_review_status": report["legal_review_status"]}, indent=2))
