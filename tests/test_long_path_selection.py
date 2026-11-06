"""Large exact selections remain bounded without absorbing unrelated staged work."""
from pathlib import Path
import tempfile
import unittest

from taskcarry.core import Core, git
from taskcarry.preservation import Preservation
from taskcarry.store import GovernanceError


class LongPathSelectionTests(unittest.TestCase):
    def test_large_selection_and_late_staged_change(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/long-path-tests'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory)
            control, repository = root / 'control', root / 'repo'
            repository.mkdir()
            Core.initialize(control)
            service = Preservation(control)
            git(repository, 'init', '--quiet')
            paths = [f'{n:04d}-' + ('synthetic-long-file-' * 5) + '.txt' for n in range(400)]
            (repository / paths[-1]).write_text('Selected synthetic content', encoding='utf-8')
            (repository / 'unrelated.txt').write_text('Keep staged intent', encoding='utf-8')
            git(repository, 'add', '--', 'unrelated.txt')
            before = git(repository, 'ls-files', '--stage', '-z').stdout
            service._selection_clean(repository, None, paths)
            self.assertEqual(before, git(repository, 'ls-files', '--stage', '-z').stdout)
            git(repository, 'add', '--', paths[-1])
            with self.assertRaises(GovernanceError) as error:
                service._selection_clean(repository, None, paths)
            self.assertEqual('PRESERVE_SELECTED_STAGED', error.exception.code)


if __name__ == '__main__':
    unittest.main()
