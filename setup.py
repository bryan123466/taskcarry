"""Build-only resource adapter; canonical skill sources stay in skills/."""
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


SKILL_NAMES = (
    "taskcarry-project-setup",
    "taskcarry-task-delivery",
    "taskcarry-governance-reconcile",
    "taskcarry-experience-recovery",
)
SKILL_REFERENCES = ("taskcarry-project-setup/references/onboarding.md",
                    "taskcarry-governance-reconcile/references/daily-governance.md")
SOURCE_ROOT = Path(__file__).resolve().parent


class BuildWithSkills(build_py):
    """Copy reviewed skills into the built package, never into the source tree."""

    def skill_sources(self):
        resources = [*(name + "/SKILL.md" for name in SKILL_NAMES), *SKILL_REFERENCES]
        for resource in resources:
            relative = Path("skills") / resource
            source = SOURCE_ROOT / relative
            if not source.is_file() or any(p.is_symlink() for p in (source, *source.parents) if p != SOURCE_ROOT.parent):
                raise RuntimeError(f"Missing canonical public skill: {relative.as_posix()}")
            yield relative, Path(self.build_lib) / "taskcarry" / "skill_data" / resource

    def run(self):
        super().run()
        if self.editable_mode:
            # Editable source use resolves the canonical skills/ directory directly.
            return
        for relative, target in self.skill_sources():
            self.mkpath(str(target.parent))
            self.copy_file(str(SOURCE_ROOT / relative), str(target))

    def get_source_files(self):
        # Also include canonical resources in source distributions produced by
        # standard PEP 517 tooling, without a generated duplicate or MANIFEST file.
        return list(dict.fromkeys([
            *super().get_source_files(),
            *(relative.as_posix() for relative, _ in self.skill_sources()),
        ]))

    def get_outputs(self, include_bytecode=True):
        outputs = super().get_outputs(include_bytecode)
        if self.editable_mode:
            return outputs
        return list(dict.fromkeys([
            *outputs,
            *(str(target) for _, target in self.skill_sources()),
        ]))


setup(cmdclass={"build_py": BuildWithSkills})
