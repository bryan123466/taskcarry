"""Resumable metadata inventory without creating a governance database.

The caller supplies authorized index pages and AI candidate groups. Nothing in
this module scans a host, executes source text, reads chat bodies or accepts a
project. Immutable revisions make interrupted writes inspectable and repeatable.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .discovery_contracts import DRAFT, PLAN
from .store import GovernanceError, _linked


MAX_BYTES = 512 * 1024
MAX_REVISIONS = 4096


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def fail(code, message, details=None):
    raise GovernanceError('DISCOVERY_' + code, message, details)


def check_text(value):
    if isinstance(value, str):
        if not value.strip() or len(value) > 2048 or '\0' in value:
            fail('BOUNDS', 'Metadata strings must be nonempty, NUL-free and at most 2048 characters.')
    elif isinstance(value, dict):
        for item in value.values():
            check_text(item)
    elif isinstance(value, list):
        for item in value:
            check_text(item)


def identity(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value):
        fail('ID', 'Use a 1-64 character ID containing letters, digits, underscores and hyphens.')
    if value.upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{n}' for n in range(1, 10)), *(f'LPT{n}' for n in range(1, 10))}:
        fail('ID', 'Use a portable ID rather than a reserved device name.')
    return value


def member_key(value):
    return value['source_id'], value['thread_id']


def publish_file(temporary, path):
    # Windows rename is atomic and refuses an existing destination. POSIX
    # rename replaces, so use atomic hardlink publication there instead.
    if os.name == 'nt':
        os.rename(temporary, path)
    else:
        os.link(temporary, path)


def normalize(draft):
    from .contracts import validate
    try:
        validate(draft, DRAFT, 'draft')
    except ValueError as error:
        fail('ARGUMENT', str(error))
    check_text(draft)
    if len(encoded(draft)) > MAX_BYTES:
        fail('BOUNDS', 'Keep the metadata draft within 512 KiB; continue another bounded discovery if needed.')
    result = json.loads(encoded(draft))
    source_ids, threads = set(), {}
    for source in result['sources']:
        sid = identity(source['source_id'])
        if sid in source_ids:
            fail('DUPLICATE', 'Source IDs must be unique; equal titles do not identify a project.')
        source_ids.add(sid)
        pages, cursors, expected = [], {}, None
        for page in source['pages']:
            cursor = page['cursor']
            if cursor in cursors:
                if cursors[cursor] != page:
                    fail('PAGE_CONFLICT', 'A repeated cursor has different content; retain the old scan and use a new source ID.')
                continue
            if cursor != expected or (pages and expected is None):
                fail('CURSOR', 'Pages must start at null and follow the preceding next_cursor without gaps or cycles.')
            if page['next_cursor'] is not None and (page['next_cursor'] == cursor or page['next_cursor'] in cursors):
                fail('CURSOR', 'A pagination cursor cycle cannot prove source coverage.')
            cursors[cursor] = page
            expected = page['next_cursor']
            pages.append(page)
            for thread in page['threads']:
                key = sid, thread['thread_id']
                if key in threads and threads[key] != thread:
                    fail('THREAD_CONFLICT', 'The same source/thread identity changed within this scan; use a fresh source ID.')
                threads[key] = thread
        source['pages'] = pages
        if source['coverage'] == 'exhausted' and (not pages or expected is not None or source['archive_scope'] == 'unknown'):
            fail('COVERAGE', 'Exhausted means the explicitly selected active or archived index ended at a null cursor.')
        if source['coverage'] == 'unavailable' and pages:
            fail('COVERAGE', 'An unavailable source has no inspected pages; retain partial coverage for interrupted reads.')
    if len(threads) > 500:
        fail('BOUNDS', 'A discovery draft supports at most 500 distinct source-qualified threads.')
    candidates = {}
    for candidate in result['candidates']:
        cid = identity(candidate['candidate_id'])
        if cid in candidates:
            fail('DUPLICATE', 'Candidate IDs must be unique even when display names match.')
        members = [member_key(m) for m in candidate['members']]
        if len(set(members)) != len(members) or any(m not in threads for m in members):
            fail('MEMBER', 'Every candidate member must be a distinct source-qualified discovered thread.')
        candidates[cid] = candidate
    selection = result.get('selection')
    selected_hash = None
    if selection:
        candidate = candidates.get(selection['candidate_id'])
        if not candidate:
            fail('SELECTION', 'Select an existing AI-proposed candidate after user review.')
        selected_hash = fingerprint({'candidate': candidate,
                                     'threads': [{'source_id': m['source_id'], **threads[member_key(m)]}
                                                 for m in candidate['members']]})
    if result.get('onboarding') and not selection:
        fail('SELECTION', 'Choose a project before linking its later onboarding.')
    return result, selected_hash, len(threads)


class Discovery:
    def __init__(self, project):
        raw = Path(project).expanduser().absolute()
        if any(_linked(p) for p in (raw, *raw.parents)) or not raw.is_dir():
            fail('PATH', 'Use an existing directory without symlink or reparse-point ancestors.')
        self.root = raw.resolve()

    def safe(self, relative, directory=False, pending_link=False):
        path = self.root / relative
        for candidate in (path, *path.parents):
            if candidate == self.root.parent:
                break
            if _linked(candidate):
                fail('PATH', 'Discovery refuses symlinks and reparse points in managed paths.')
            if candidate != path and candidate.exists() and not candidate.is_dir():
                fail('CONFLICT', 'A discovery parent path is an existing file and was preserved.')
        if not path.resolve().is_relative_to(self.root):
            fail('PATH', 'Discovery metadata must stay within its selected governance directory.')
        if path.exists():
            if (directory and not path.is_dir()) or (not directory and not path.is_file()):
                fail('CONFLICT', 'An existing managed path has a different file type; it was preserved.')
            if not directory and path.stat().st_nlink > 1:
                # If the process died between no-replace publication and
                # unlinking its temporary name, both local names are the same
                # immutable revision. Permit only this exact two-link effect.
                info = path.stat()
                matches = []
                if pending_link and info.st_nlink == 2:
                    for other in path.parent.iterdir():
                        if other != path and not _linked(other) and other.is_file():
                            same = (other.stat().st_dev, other.stat().st_ino) == (info.st_dev, info.st_ino)
                            pair = ((re.fullmatch(r'[0-9]{8}\.json', path.name) and re.fullmatch(r'\.taskcarry-discovery-[A-Za-z0-9_-]+\.tmp', other.name))
                                    or (re.fullmatch(r'[0-9]{8}\.json', other.name) and re.fullmatch(r'\.taskcarry-discovery-[A-Za-z0-9_-]+\.tmp', path.name)))
                            if same and pair:
                                matches.append(other)
                if len(matches) != 1:
                    fail('PATH', 'Discovery refuses multiply-linked metadata files outside its interrupted atomic publication.')
        return path

    def root_identity(self):
        info = self.root.stat()
        # Host MCP clients may use IEEE-754 JSON numbers; preserve large file
        # IDs exactly rather than losing bits during a plan round trip.
        return {'device': str(info.st_dev), 'inode': str(info.st_ino)}

    def state_binding(self, writable=False):
        from .core import Core
        result = Core.identify(self.root)
        if result['state'] == 'uninitialized':
            return None
        if result['state'] != 'compatible':
            fail('STATE', 'Inspect existing governance metadata before saving a discovery draft.', result)
        if writable and result['source'].get('writer_state') == 'standby':
            raise GovernanceError('RECOVERY_STANDBY', 'A restored standby cannot save discovery revisions before writer activation.')
        return {k: result['source'].get(k) for k in ('source_id', 'replica_id', 'identity_scope', 'writer_state')}

    def current(self, discovery_id):
        relative = '.taskcarry-onboarding/discovery/' + identity(discovery_id)
        directory = self.safe(relative, directory=True)
        if not directory.exists():
            return None
        entries = []
        for index, path in enumerate(directory.iterdir()):
            if index >= MAX_REVISIONS * 2:
                fail('BOUNDS', 'Discovery file enumeration exceeds its bounded limit.')
            # A process crash can leave its own random temporary file. It is
            # not a committed revision and is never adopted or deleted here.
            if re.fullmatch(r'\.taskcarry-discovery-[A-Za-z0-9_-]+\.tmp', path.name):
                self.safe(relative + '/' + path.name, pending_link=True)
                continue
            if not re.fullmatch(r'[0-9]{8}\.json', path.name):
                fail('CONFLICT', 'An unrecognized discovery file was preserved; inspect it before proceeding.')
            entries.append(path.name)
            if len(entries) > MAX_REVISIONS:
                fail('BOUNDS', 'Discovery revision history exceeds its bounded limit.')
        if not entries:
            return None
        entries.sort()
        if entries != [f'{n:08d}.json' for n in range(1, len(entries) + 1)]:
            fail('HISTORY', 'Discovery revision history has a gap; do not reinterpret an older selection as current.')
        path = self.safe(relative + '/' + entries[-1], pending_link=True)
        if path.stat().st_size > MAX_BYTES + 16384:
            fail('BOUNDS', 'The discovery record exceeds its bounded size.')
        try:
            record = json.loads(path.read_bytes())
            plan = record['plan']
            self.check_plan(plan)
            if (set(record) != {'format', 'revision', 'plan'} or record['format'] != 1
                    or record['revision'] != len(entries) or plan['expected_revision'] != len(entries) - 1
                    or plan['discovery_id'] != discovery_id):
                raise ValueError('Invalid revision record')
        except (ValueError, KeyError, TypeError) as error:
            fail('RECORD', 'The current discovery record is invalid and was preserved.', str(error))
        return record

    def check_plan(self, plan):
        from .contracts import validate
        try:
            validate(plan, PLAN, 'plan')
        except ValueError as error:
            fail('PLAN', str(error))
        check_text(plan)
        if len(encoded(plan)) > MAX_BYTES + 8192:
            fail('BOUNDS', 'The complete plan exceeds its bounded size.')
        body = {k: v for k, v in plan.items() if k != 'plan_id'}
        if plan['plan_id'] != 'discovery-' + fingerprint(body):
            fail('PLAN', 'Execute the complete unchanged plan returned by discovery plan.')
        normalized, selected_hash, _ = normalize(plan['draft'])
        if normalized != plan['draft'] or selected_hash != plan['selection_fingerprint']:
            fail('PLAN', 'The planned metadata or selected scope fingerprint does not match.')

    def check_binding(self, plan):
        if (plan['root'] != str(self.root) or plan['root_identity'] != self.root_identity()
                or plan['state_binding'] != self.state_binding(writable=True)):
            fail('BINDING', 'The selected root, local replica or initialization state changed; prepare a new local plan.')

    def link(self, draft, selected_hash):
        link = draft.get('onboarding')
        if not link:
            return None
        from .core import Core
        if link['selection_fingerprint'] != selected_hash:
            fail('ONBOARDING', 'The onboarding link belongs to a different selected discovery scope.')
        state = Core(self.root)
        record = state.store.get('onboarding', identity(link['onboarding_id']))
        if not record or record['scope_fingerprint'] != link['scope_fingerprint']:
            fail('ONBOARDING', 'Read the actual onboarding and bind its current scope fingerprint.')
        candidate = next(c for c in draft['candidates'] if c['candidate_id'] == draft['selection']['candidate_id'])
        selected = {member_key(m) for m in candidate['members']}
        mappings = link['windows']
        if ({member_key(m) for m in mappings} != selected or len(mappings) != len(selected)
                or len({m['window_thread_id'] for m in mappings}) != len(mappings)):
            fail('ONBOARDING', 'Map every selected source/thread once to distinct actual onboarding windows.')
        actual = {w['thread_id']: w['source_ref'] for w in record['scope']['windows']}
        if any(actual.get(m['window_thread_id']) != m['source_ref'] for m in mappings):
            fail('ONBOARDING', 'The mapped window and source reference must match actual onboarding scope.')
        return {'onboarding_id': link['onboarding_id'], 'scope_fingerprint': record['scope_fingerprint'],
                'binding_current': True, 'acceptance_inherited': False}

    @contextmanager
    def lock(self, discovery_id):
        relative = '.taskcarry-onboarding/discovery'
        directory = self.safe(relative, directory=True)
        directory.mkdir(parents=True, exist_ok=True)
        path = self.safe(relative + '/' + discovery_id + '.lock')
        with path.open('a+b') as stream:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0, os.SEEK_END)
                if stream.tell() == 0:
                    stream.write(b'0')
                    stream.flush()
                stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    fail('BUSY', 'Another process is saving this discovery; inspect status before retrying.', str(error))
            else:
                import fcntl
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error:
                    fail('BUSY', 'Another process is saving this discovery; inspect status before retrying.', str(error))
            yield

    def publish(self, relative, data):
        path = self.safe(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.taskcarry-discovery-', suffix='.tmp', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            # Atomic no-replace publication: never overwrite a user file, even
            # if a non-cooperating writer ignores our advisory lock.
            try:
                publish_file(temporary, path)
            except FileExistsError:
                fail('CONFLICT', 'The revision destination appeared during saving; inspect its actual effect.')
            if os.name != 'nt':
                descriptor = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def report(self, discovery_id, record, effects=False, reused=False):
        if not record:
            return {'discovery_id': discovery_id, 'revision': 0, 'state': 'NOT_STARTED',
                    'effects_executed': False, 'control_initialized_by_discovery': False}
        plan = record['plan']
        draft, selected_hash, count = normalize(plan['draft'])
        link = None
        if draft.get('onboarding'):
            try:
                link = self.link(draft, selected_hash)
            except GovernanceError as error:
                link = {'binding_current': False, 'acceptance_inherited': False, 'error': {'code': error.code, 'message': error.message}}
        local_binding = plan['root'] == str(self.root) and plan['root_identity'] == self.root_identity()
        if local_binding and plan['state_binding'] is not None:
            try:
                local_binding = plan['state_binding'] == self.state_binding()
            except GovernanceError:
                local_binding = False
        if link and not local_binding:
            link = {'binding_current': False, 'acceptance_inherited': False,
                    'error': {'code': 'DISCOVERY_BINDING', 'message': 'Review this copied or changed local replica before using its historical onboarding link.'}}
        return {'discovery_id': discovery_id, 'revision': record['revision'], 'fingerprint': fingerprint(record),
                'state': 'REVIEW_REQUIRED' if not local_binding else 'SELECTED' if selected_hash else 'AWAITING_SELECTION' if draft['candidates'] else 'DISCOVERING',
                'draft': draft, 'selection_fingerprint': selected_hash, 'distinct_threads': count,
                'onboarding_link': link, 'local_binding_matches': local_binding,
                'selection_current': bool(selected_hash and local_binding),
                'effects_executed': effects, 'reused': reused, 'control_initialized_by_discovery': False,
                'source_text_is_instruction': False, 'chat_bodies_read': False,
                'coverage_scope': 'caller_supplied_index_pages_only', 'all_chats_verified': False,
                'acceptance_inherited': False, 'native_acceptance_verified': False,
                'next_step': 'Review the copied or changed local replica and obtain a fresh user selection before reading selected history.'
                             if not local_binding else 'Read only the user-selected sources, then prepare or resume their actual onboarding.'
                             if selected_hash else 'Continue saved source cursors and ask the user to choose an AI-proposed project.'}

    def discovery(self, discovery_id, action='status', expected_revision=None, draft=None, plan=None):
        identity(discovery_id)
        if action == 'status':
            if any(v is not None for v in (expected_revision, draft, plan)):
                fail('ARGUMENT', 'Status only accepts discovery_id.')
            return self.report(discovery_id, self.current(discovery_id))
        if action == 'plan':
            if plan is not None or expected_revision is None:
                fail('ARGUMENT', 'Plan requires a complete bounded draft and the current expected_revision, initially zero.')
            current = self.current(discovery_id)
            revision = current['revision'] if current else 0
            if expected_revision != revision or revision >= MAX_REVISIONS:
                fail('CHANGED', 'Read discovery status before planning the next revision.', {'revision': revision})
            normalized, selected_hash, _ = normalize(draft)
            selection_guard = None
            binding = self.state_binding()
            if current:
                previous = current['plan']
                if previous['draft'].get('selection'):
                    selection_guard = {key: previous[key] for key in ('selection_fingerprint', 'root', 'root_identity', 'state_binding')}
                    selection_guard['confirmation_ref'] = previous['draft']['selection']['confirmation_ref']
                else:
                    selection_guard = previous['selection_guard']
                if (previous['root'] != str(self.root) or previous['root_identity'] != self.root_identity()
                        or (previous['state_binding'] is not None and previous['state_binding'] != self.state_binding())):
                    if normalized.get('onboarding') or (normalized.get('selection') and normalized['selection'].get('confirmation_ref') == previous['draft'].get('selection', {}).get('confirmation_ref')):
                        fail('BINDING', 'A copied discovery needs a fresh local user selection and a separately verified onboarding link.')
                prior_sources = {s['source_id']: s for s in previous['draft']['sources']}
                for source in normalized['sources']:
                    prior = prior_sources.pop(source['source_id'], None)
                    if prior and (source['label'] != prior['label'] or source['archive_scope'] != prior['archive_scope']
                                  or source['pages'][:len(prior['pages'])] != prior['pages']):
                        fail('PAGE_CONFLICT', 'Retain already recorded pages; use a new source ID for a refreshed index.')
                if prior_sources:
                    fail('PAGE_CONFLICT', 'Retain prior source coverage when continuing this discovery.')
            new_selection = normalized.get('selection')
            if selection_guard and new_selection:
                same_scope = selection_guard['selection_fingerprint'] == selected_hash
                same_local = (selection_guard['root'] == str(self.root) and selection_guard['root_identity'] == self.root_identity()
                              and (selection_guard['state_binding'] is None or selection_guard['state_binding'] == binding))
                if (not same_scope or not same_local) and selection_guard['confirmation_ref'] == new_selection['confirmation_ref']:
                    fail('CONFIRMATION', 'A changed or copied selection needs a new user confirmation reference, including after an unselected draft.')
            self.link(normalized, selected_hash)
            body = {'format': 1, 'root': str(self.root), 'root_identity': self.root_identity(),
                    'state_binding': binding, 'discovery_id': discovery_id,
                    'expected_revision': revision, 'expected_fingerprint': fingerprint(current) if current else None,
                    'draft': normalized, 'selection_fingerprint': selected_hash, 'selection_guard': selection_guard}
            result = {**body, 'plan_id': 'discovery-' + fingerprint(body)}
            return {'plan': result, 'effects_executed': False, 'control_initialized_by_discovery': False,
                    'selection_fingerprint': selected_hash, 'acceptance_inherited': False}
        if action != 'execute' or plan is None or expected_revision is not None or draft is not None:
            fail('ARGUMENT', 'Execute only accepts discovery_id and the complete unchanged plan.')
        self.check_plan(plan)
        if discovery_id != plan['discovery_id']:
            fail('PLAN', 'The plan belongs to a different discovery ID.')
        self.check_binding(plan)
        with self.lock(discovery_id):
            self.check_binding(plan)
            current = self.current(discovery_id)
            if current and current['plan'] == plan:
                return self.report(discovery_id, current, reused=True)
            if ((current['revision'] if current else 0) != plan['expected_revision']
                    or (fingerprint(current) if current else None) != plan['expected_fingerprint']):
                fail('CHANGED', 'The discovery changed after planning; read current status before proceeding.')
            reviewed = self.discovery(discovery_id, 'plan', plan['expected_revision'], plan['draft'])['plan']
            if reviewed != plan:
                fail('PLAN', 'The plan no longer matches its current metadata, selection or local bindings.')
            if current and all(current['plan'][key] == plan[key] for key in
                               ('root', 'root_identity', 'state_binding', 'draft', 'selection_fingerprint')):
                return self.report(discovery_id, current, reused=True)
            record = {'format': 1, 'revision': plan['expected_revision'] + 1, 'plan': plan}
            relative = f'.taskcarry-onboarding/discovery/{discovery_id}/{record["revision"]:08d}.json'
            self.publish(relative, encoded(record))
            observed = self.current(discovery_id)
            if observed != record:
                fail('EFFECT', 'Inspect the actual saved revision before retrying an uncertain save.')
            return self.report(discovery_id, observed, effects=True)
