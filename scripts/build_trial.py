"""Build trial artifacts from a frozen positive allowlist; inspect wheel parity."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from taskcarry import __version__

ROOT_FILES = {"README.md", "README.zh-CN.md", "README.zh-TW.md", "START_HERE.md", "LICENSE", "LICENSE_SCOPE.md", "SECURITY.md", "CONTRIBUTING.md", "pyproject.toml", "setup.py", ".gitignore", ".gitattributes", "AGENTS.md"}
DIRECTORIES = {"taskcarry", "skills", "docs", "templates", "examples", "tests", "scripts", ".github"}
EXTENSIONS = {".py", ".md", ".json", ".toml", ".html", ".css", ".js", ".yaml", ".yml", ".txt", ".svg", ".csv"}
# This illustrative redraw was visually reviewed; original project screenshots
# are not allowed. A changed or additional binary must be reviewed explicitly.
REVIEWED_BINARY_ASSETS = {
    "docs/assets/workspace-sidebar-example.png": "dfc75af11cf1a2950f16479b70e95346b97fb0a06f73fc0fbdfca6dbacfaee22",
    "docs/assets/social-preview.png": "8763f806449c8aa1ee5cb7e4a3680bd2f4d3c96ba3c0a08e5bd107bf51b7db5a",
}
EXCLUDED = {"__pycache__", ".taskcarry", ".venv", ".git", "node_modules", "dist", "build", "local"}
SKILLS = {"taskcarry-project-setup", "taskcarry-task-delivery", "taskcarry-governance-reconcile", "taskcarry-experience-recovery"}
SKILL_REFERENCES = {"taskcarry-project-setup/references/onboarding.md",
                    "taskcarry-governance-reconcile/references/daily-governance.md"}
REQUIRED = {"docs/VALIDATION.md", "docs/VALIDATION_RESULTS.json", "README.md", "README.zh-CN.md", "README.zh-TW.md", "LICENSE", "LICENSE_SCOPE.md", "pyproject.toml", "setup.py"}
# Deliberately invalid path in a public traversal-rejection test fixture.
SYNTHETIC_ABSOLUTE_LITERALS = {"C:/outside.txt"}
# Reviewed public tutorial root, permitted only in the named example resources.
# This does not permit real user paths, traversal, another drive, or secrets.
SYNTHETIC_EXAMPLE_FILES = {
    "docs/en/windows-example.md", "docs/zh-CN/windows-example.md", "docs/zh-TW/windows-example.md",
    "docs/en/manual-setup.md", "docs/zh-CN/manual-setup.md", "docs/zh-TW/manual-setup.md",
    "examples/windows_quickstart/bootstrap.py",
}
REQUIRED.update({f"docs/{language}/manual-setup.md" for language in ("en", "zh-CN", "zh-TW")})
REQUIRED.update({f"docs/{language}/updating.md" for language in ("en", "zh-CN", "zh-TW")})
REQUIRED.update({"skills/" + name for name in SKILL_REFERENCES})
# The documented fresh-install example must be runnable from the archive.
REQUIRED.update({"examples/quality_forms/fixture/requirements.md",
                 "examples/quality_forms/fixture/forms/inspection.csv",
                 "examples/quality_forms/fixture/quality/corrective-actions.csv",
                 "examples/quality_forms/fixture/review/review-checklist.md"})
REQUIRED.update({"examples/governed-project/README.md", "examples/governed-project/scenario.json"})
REQUIRED.update({"docs/GOVERNANCE_API.md", "examples/complete-governance/README.md",
                 "examples/complete-governance/scenario.json"})
REQUIRED.update({"examples/complete-governance/fixture/" + name for name in
                 ("PROTOCOL.md", "normal_frames.txt", "expected.csv", "replay.py")})
REQUIRED.update({f"docs/{language}/user-feedback-examples.md" for language in ("en", "zh-CN", "zh-TW")})


def sha(data):
    return hashlib.sha256(data).hexdigest()


def linked(path):
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def reviewed_example_path(name, value):
    if name not in SYNTHETIC_EXAMPLE_FILES:
        return False
    normalized = value.replace("\\", "/")
    if not re.fullmatch(r"C:" + r"/TaskCarry(?:/[A-Za-z0-9_.-]+)*/?", normalized):
        return False
    return all(part not in {".", ".."} for part in normalized.split("/"))


def reviewed_example_spans(name, text):
    """Allow only whole quoted or whole-line tutorial paths, never prefixes."""
    if name not in SYNTHETIC_EXAMPLE_FILES:
        return set()
    spans = set()
    quoted = re.compile(r'''(?P<quote>["'`])(?P<value>[A-Za-z]:[\\/][^\r\n]*?)(?P=quote)''')
    standalone = re.compile(r'''(?m)^[ \t]*(?P<value>[A-Za-z]:[\\/][^\r\n]*?)[ \t]*\r?$''')
    for pattern in (quoted, standalone):
        for match in pattern.finditer(text):
            if reviewed_example_path(name, match.group("value")):
                spans.add(match.span("value"))
    return spans


def files():
    """Only named roots and textual extensions; no link following or stale assets."""
    selected = []
    for directory, children, filenames in os.walk(ROOT, followlinks=False):
        base = Path(directory)
        children[:] = sorted(name for name in children if name not in EXCLUDED
                             and not name.endswith(".egg-info")
                             and not linked(base / name)
                             and (base != ROOT or name in DIRECTORIES)
                             and (base != ROOT / "taskcarry" or name != "skill_data"))
        for name in sorted(filenames):
            path = base / name
            if linked(path) or not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if (relative.as_posix() in ROOT_FILES or relative.as_posix() in REVIEWED_BINARY_ASSETS
                    or (relative.parts[0] in DIRECTORIES and path.suffix.lower() in EXTENSIONS)):
                selected.append(path)
    return sorted(selected)


def screen_content(contents, deny_tokens=()):
    """Release hygiene, not complete secret or private-data detection."""
    host_roots = [str(ROOT).replace("\\", "/").casefold(), str(Path.home()).replace("\\", "/").casefold()]
    findings = []
    absolute_pattern = re.compile(r'''(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/])[^"'`\s<>()\[\]{},;]*''')
    for name, content in contents.items():
        if name in REVIEWED_BINARY_ASSETS:
            if sha(content) != REVIEWED_BINARY_ASSETS[name] or not content.startswith(b"\x89PNG\r\n\x1a\n"):
                findings.append({"path": name, "kind": "reviewed_asset_changed"})
            continue
        try:
            text = content.decode("utf-8-sig")
        except UnicodeError:
            findings.append({"path": name, "kind": "unexpected_binary"})
            continue
        normalized = text.replace("\\\\", "/").replace("\\", "/").casefold()
        if any(root in normalized for root in host_roots):
            findings.append({"path": name, "kind": "current_host_absolute_path"})
        if any(token.casefold() in text.casefold() for token in deny_tokens if token):
            findings.append({"path": name, "kind": "caller_denied_token"})
        example_spans = reviewed_example_spans(name, text)
        for match in absolute_pattern.finditer(text):
            value = match.group()
            if (value.replace("\\", "/") not in SYNTHETIC_ABSOLUTE_LITERALS
                    and match.span() not in example_spans):
                findings.append({"path": name, "kind": "unreviewed_absolute_path"})
                break
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bsk-[A-Za-z0-9]{32,}", text):
            findings.append({"path": name, "kind": "possible_secret"})
    if findings:
        raise RuntimeError("Release content screening failed: " + json.dumps(findings, ensure_ascii=False))
    return {"screened_files": len(contents), "findings": [], "scope": "allowlist, host paths, caller deny tokens, common secret patterns; manual scope review remains required"}


def validate_download_entry(contents):
    """Refuse a product whose current download sends users to another version."""
    entry = contents["START_HERE.md"].decode("utf-8")
    downloads = re.findall(r"https://github\.com/bryan123466/taskcarry/releases/tag/v([^\s)\"<>]+)", entry)
    if not downloads or any(version != __version__ for version in downloads):
        raise RuntimeError("The current download entry must match the package version")
    for language in ("en", "zh-CN", "zh-TW"):
        for guide in ("windows-example", "updating"):
            path = f"docs/{language}/{guide}.md"
            if path not in contents or f"]({path})" not in entry:
                raise RuntimeError("The download entry needs both user routes in all three languages")


def _git_bytes(*arguments, input_bytes=None):
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '--no-replace-objects', '-C', str(ROOT), *arguments],
                            input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=environment, timeout=60, check=False)
    if result.returncode:
        raise RuntimeError('Cannot read the reviewed Git source: ' + result.stderr.decode('utf-8', 'replace')[:2000])
    return result.stdout


def _allowed_committed_path(name):
    parts = name.split('/')
    if (not parts or any(part in EXCLUDED or part.endswith('.egg-info') for part in parts)
            or name.startswith('taskcarry/skill_data/')):
        return False
    return (name in ROOT_FILES or name in REVIEWED_BINARY_ASSETS
            or (parts[0] in DIRECTORIES and Path(name).suffix.lower() in EXTENSIONS))


def freeze_commit(contents, source_commit):
    """Validate checkout parity, then return exact blob bytes, including skills.

    CRLF checkout conversions are tolerated only for UTF-8 text. They never
    become the packaged bytes. Membership comes from the committed tree too,
    so deleted or newly untracked allowed files cannot silently change scope.
    No checkout, index, ref, output directory or temporary file is written.
    """
    if not isinstance(source_commit, str) or not re.fullmatch(r'[0-9a-f]{40}', source_commit):
        raise ValueError('Provide the full reviewed source commit')
    if _git_bytes('cat-file', '-t', source_commit).strip() != b'commit':
        raise RuntimeError('The reviewed source must identify a commit object')
    entries = {}
    for line in _git_bytes('ls-tree', '-r', '-z', '--full-tree', source_commit).split(b'\0'):
        if not line:
            continue
        metadata, encoded_name = line.split(b'\t', 1)
        name = encoded_name.decode('utf-8')
        mode, kind, oid = metadata.decode('ascii').split()
        if not _allowed_committed_path(name):
            continue
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise RuntimeError('Reviewed source contains a non-regular allowed path: ' + name)
        entries[name] = oid
    canonical = {name: data for name, data in contents.items() if not name.startswith('taskcarry/skill_data/')}
    if set(canonical) != set(entries):
        raise RuntimeError('Package source membership differs from reviewed commit: ' + json.dumps({
            'missing_from_checkout': sorted(set(entries) - set(canonical)),
            'not_in_commit': sorted(set(canonical) - set(entries))}))
    objects = list(dict.fromkeys(entries.values()))
    batch = _git_bytes('cat-file', '--batch', input_bytes=('\n'.join(objects) + '\n').encode('ascii')) if objects else b''
    blobs, offset = {}, 0
    for expected in objects:
        end = batch.find(b'\n', offset)
        if end == -1:
            raise RuntimeError('Incomplete Git blob response')
        oid, kind, size = batch[offset:end].decode('ascii').split()
        size = int(size)
        start, offset = end + 1, end + 2 + size
        if oid != expected or kind != 'blob' or batch[offset - 1:offset] != b'\n':
            raise RuntimeError('Unexpected Git blob response')
        content = batch[start:start + size]
        if hashlib.sha1(b'blob ' + str(size).encode('ascii') + b'\0' + content).hexdigest() != oid:
            raise RuntimeError('The stored Git blob does not match its object identity')
        blobs[oid] = content
    if offset != len(batch):
        raise RuntimeError('Unexpected trailing Git blob bytes')
    frozen = {}
    for name, oid in entries.items():
        committed, checkout = blobs[oid], canonical[name]
        if committed != checkout:
            try:
                committed.decode('utf-8')
                checkout.decode('utf-8')
            except UnicodeError:
                raise RuntimeError('Package source differs from reviewed commit: ' + name)
            if name in REVIEWED_BINARY_ASSETS or committed.replace(b'\r\n', b'\n') != checkout.replace(b'\r\n', b'\n'):
                raise RuntimeError('Package source differs from reviewed commit: ' + name)
        frozen[name] = committed
    resources = [*(skill + '/SKILL.md' for skill in sorted(SKILLS)), *sorted(SKILL_REFERENCES)]
    expected_generated = {'taskcarry/skill_data/' + resource for resource in resources}
    if set(contents) - set(canonical) != expected_generated:
        raise RuntimeError('Generated skill membership differs from the reviewed resources')
    for resource in resources:
        source_name = 'skills/' + resource
        if source_name not in frozen:
            raise RuntimeError('Reviewed source lacks a canonical skill resource: ' + source_name)
        frozen['taskcarry/skill_data/' + resource] = frozen[source_name]
    return frozen


def snapshot(deny_tokens=(), source_commit=None):
    contents = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in files()}
    missing = sorted(REQUIRED - set(contents))
    if missing:
        raise RuntimeError("Complete validation and release documentation before packaging: " + ", ".join(missing))
    metadata = tomllib.loads(contents["pyproject.toml"].decode("utf-8"))
    if metadata["project"]["version"] != __version__:
        raise RuntimeError("Package and implementation versions differ")
    validate_download_entry(contents)
    if not isinstance(json.loads(contents["docs/VALIDATION_RESULTS.json"]), dict):
        raise RuntimeError("Validation results must be a structured object")
    actual_skills = {name.split("/")[1] for name in contents if name.startswith("skills/") and name.endswith("/SKILL.md")}
    if actual_skills != SKILLS:
        raise RuntimeError("The release must contain the four reviewed public skills")
    for skill in sorted(SKILLS):
        contents[f"taskcarry/skill_data/{skill}/SKILL.md"] = contents[f"skills/{skill}/SKILL.md"]
    for resource in sorted(SKILL_REFERENCES):
        contents["taskcarry/skill_data/" + resource] = contents["skills/" + resource]
    if source_commit is not None:
        contents = freeze_commit(contents, source_commit)
    screening = screen_content(contents, deny_tokens)
    return contents, screening


def build_dependencies():
    versions = {}
    for name in ("pip", "setuptools", "wheel"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(f"Build environment lacks {name}; use a dedicated build environment") from exc
    if int(versions["setuptools"].split(".")[0]) < 68:
        raise RuntimeError("setuptools >= 68 is required by pyproject.toml")
    return versions


def inspect_wheel(wheel, source, deny_tokens=()):
    expected = {name: data for name, data in source.items() if name.startswith("taskcarry/")}
    if not {f"taskcarry/skill_data/{skill}/SKILL.md" for skill in SKILLS}.issubset(expected):
        raise RuntimeError("Frozen wheel sources lack one or more required skills")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("Wheel contains duplicate members")
        packaged = {}
        for info in archive.infolist():
            name = info.filename
            if info.is_dir():
                continue
            if name.startswith("/") or ".." in Path(name).parts or "\\" in name or stat.S_ISLNK(info.external_attr >> 16):
                raise RuntimeError("Wheel contains an unsafe member")
            if not (name.startswith("taskcarry/") or re.match(r"taskcarry-[^/]+\.dist-info/", name)):
                raise RuntimeError("Wheel contains a file outside the allowed package and metadata")
            if not name.startswith("taskcarry/"):
                relative_metadata = name.split(".dist-info/", 1)[1]
                if relative_metadata not in {"METADATA", "WHEEL", "RECORD", "entry_points.txt", "top_level.txt", "licenses/LICENSE", "licenses/LICENSE_SCOPE.md", "LICENSE", "LICENSE_SCOPE.md"}:
                    raise RuntimeError("Wheel contains unreviewed distribution metadata")
            packaged[name] = archive.read(info)
        actual = {name: data for name, data in packaged.items() if name.startswith("taskcarry/")}
        if set(actual) != set(expected):
            raise RuntimeError("Wheel package membership differs from the frozen allowlist")
        if any(actual[name] != data for name, data in expected.items()):
            raise RuntimeError("Wheel changed a frozen package file")
        for required_name in ("METADATA", "WHEEL", "RECORD", "entry_points.txt"):
            if not any(name.endswith(".dist-info/" + required_name) for name in packaged):
                raise RuntimeError("Wheel lacks required package metadata: " + required_name)
        screen_content(packaged, deny_tokens)
    return {"verified_package_files": len(expected), "skill_count": len(SKILLS), "membership_and_hashes_match": True}


def product_contents(contents):
    """User distribution: working tools and usage docs, no maintenance evidence."""
    excluded_files = {"AGENTS.md", "CONTRIBUTING.md", "docs/VALIDATION.md", "docs/VALIDATION_RESULTS.json",
                      "docs/TESTER_START.md", "docs/TESTER_START.zh-CN.md",
                      "docs/en/trial-guide.md", "docs/zh-CN/trial-guide.md"}
    excluded_prefixes = ("tests/", "scripts/", ".github/", "examples/quality_forms/reference/")
    result = {name: data for name, data in contents.items()
              if name not in excluded_files and not name.startswith(excluded_prefixes)}
    required = {"START_HERE.md", "docs/en/getting-started.md", "docs/zh-CN/getting-started.md",
                "docs/en/windows-example.md", "docs/zh-CN/windows-example.md", "docs/zh-TW/windows-example.md",
                "examples/windows_quickstart/bootstrap.py"}
    if not required.issubset(result):
        raise RuntimeError("Product package needs complete project onboarding documentation")
    if not {f"docs/{language}/manual-setup.md" for language in ("en", "zh-CN", "zh-TW")}.issubset(result):
        raise RuntimeError("Product package needs the three manual fallback guides")
    if not {f"docs/{language}/updating.md" for language in ("en", "zh-CN", "zh-TW")}.issubset(result):
        raise RuntimeError("Product package needs the three existing-user update guides")
    if not {"skills/" + name for name in SKILL_REFERENCES}.issubset(result):
        raise RuntimeError("Product package needs the public onboarding skill references")
    return result


def build(destination, replace=False, deny_tokens=(), profile="source", source_commit=None):
    # No output or source mutation before the required evidence is present.
    contents, screening = snapshot(deny_tokens, source_commit)
    if profile not in {"source", "product"}:
        raise ValueError("Unknown release profile")
    if profile == "product":
        contents = product_contents(contents)
        screening = screen_content(contents, deny_tokens)
    dependencies = build_dependencies()
    destination = Path(destination).resolve()
    if destination == ROOT or destination.is_relative_to(ROOT):
        raise RuntimeError("Release output must be outside the source repository")
    destination.parent.mkdir(parents=True, exist_ok=True)
    prefix = "taskcarry-" + __version__
    with tempfile.TemporaryDirectory(prefix="taskcarry-build-", dir=destination.parent) as temporary:
        temporary = Path(temporary)
        stage, output = temporary / "source", temporary / "output"
        stage.mkdir()
        output.mkdir()
        for name, content in contents.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation", "--wheel-dir", str(output), str(stage)], check=True, timeout=180)
        wheels = list(output.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one newly built wheel")
        wheel_check = inspect_wheel(wheels[0], contents, deny_tokens)
        archive_contents = dict(contents)
        if profile == "product":
            archive_contents["packages/" + wheels[0].name] = wheels[0].read_bytes()
            archive_contents["SHA256SUMS.txt"] = (sha(wheels[0].read_bytes()) + "  packages/" + wheels[0].name + "\n").encode("utf-8")
        manifest = {"product": "TaskCarry", "version": __version__, "source_commit": source_commit,
                    "files": [{"path": name, "sha256": sha(content), "bytes": len(content)} for name, content in sorted(archive_contents.items())]}
        archive = output / (prefix + ("-product" if profile == "product" else "") + ".zip")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            payloads = {**archive_contents, "RELEASE_MANIFEST.json": json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")}
            for name, content in sorted(payloads.items()):
                info = zipfile.ZipInfo(prefix + "/" + name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                zipped.writestr(info, content)
        with zipfile.ZipFile(archive) as zipped:
            expected_names = {prefix + "/" + name for name in payloads}
            if len(zipped.namelist()) != len(expected_names) or set(zipped.namelist()) != expected_names:
                raise RuntimeError("Source archive membership differs from its positive allowlist")
            if zipped.testzip() is not None or any(zipped.read(prefix + "/" + name) != data for name, data in payloads.items()):
                raise RuntimeError("Source archive bytes do not match the frozen source")
        candidates = [archive, wheels[0]]
        if source_commit is not None:
            from taskcarry.updates import build_release_manifest, MANIFEST_NAME
            release_manifest = build_release_manifest(__version__, source_commit,
                [{'name': path.name, 'size': path.stat().st_size, 'sha256': sha(path.read_bytes())} for path in candidates],
                required_actions=['Preserve the existing project and custom rules; use the existing-governance update guide.',
                                  'Prepare a separate runtime, review setup/connect, then verify affected native windows.',
                                  'Explicitly upgrade derived indexes when the installed tools report that context needs them.'])
            release_path = output / MANIFEST_NAME
            release_path.write_text(json.dumps(release_manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            candidates.append(release_path)
        summary = {"version": __version__, "profile": profile, "source_file_count": len(contents), "build_dependencies": dependencies,
                   "source_commit": source_commit, "release_manifest_created": source_commit is not None,
                   "content_screening": screening, "wheel_verification": wheel_check,
                   "source_verification": {"membership_and_hashes_match": True, "manifest_present": True,
                                           "source_commit_verified": source_commit is not None,
                                           "payload_origin": "git_blobs" if source_commit is not None else "checkout_snapshot",
                                           "generated_skill_resources": len(SKILLS) + len(SKILL_REFERENCES)},
                   "archives": [{"name": path.name, "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())} for path in candidates]}
        (output / "SHA256SUMS.txt").write_text("".join(sha(path.read_bytes()) + "  " + path.name + "\n" for path in candidates), encoding="utf-8")
        (output / "BUILD_RESULT.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        output_files = list(output.iterdir())
        if not replace and any((destination / path.name).exists() for path in output_files):
            raise RuntimeError("Output exists; use a new directory or explicitly pass --replace")
        destination.mkdir(parents=True, exist_ok=True)
        for path in output_files:
            os.replace(path, destination / path.name)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Output directory outside the repository")
    parser.add_argument("--check", action="store_true", help="Read-only checks; no wheel build")
    parser.add_argument("--replace", action="store_true", help="Explicitly replace same-named artifacts after checks pass")
    parser.add_argument("--deny-token", action="append", default=[], help="Additional private term excluded from release")
    parser.add_argument("--profile", choices=["source", "product"], default="source", help="Product omits maintainer evidence and bundles the installable wheel")
    parser.add_argument("--source-commit", help="Exact reviewed source SHA; verify all source bytes and emit the separate update manifest")
    arguments = parser.parse_args()
    if arguments.check:
        content, screening = snapshot(arguments.deny_token, arguments.source_commit)
        if arguments.profile == "product":
            content = product_contents(content)
            screening = screen_content(content, arguments.deny_token)
        print(json.dumps({"ready": True, "source_file_count": len(content), "build_dependencies": build_dependencies(), "screening": screening}, indent=2))
    elif not arguments.out:
        parser.error("--out is required unless --check is used")
    else:
        print(json.dumps(build(arguments.out, arguments.replace, arguments.deny_token, arguments.profile, arguments.source_commit), indent=2))
