"""Durable local records and a nonblocking operating-system mutation guard."""
from __future__ import annotations

from contextlib import contextmanager, closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
import uuid


TERMINAL_STATES = frozenset(('accepted', 'committed', 'complete', 'completed', 'superseded',
                             'cancelled', 'dismissed', 'finalized', 'adopted'))
CURRENT_PROJECTION_VERSION = 1


class GovernanceError(Exception):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details


def now():
    return datetime.now(timezone.utc).isoformat()


def _linked(path):
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)
    except FileNotFoundError:
        return False


class Store:
    def __init__(self, project, create=False):
        raw_root = Path(project).expanduser().absolute()
        if any(_linked(p) for p in (raw_root, *raw_root.parents)):
            raise GovernanceError('UNSAFE_METADATA', 'The project location cannot traverse symbolic links or junctions.')
        self.root = raw_root.resolve()
        self.directory = self.root / '.taskcarry'
        self.path = self.directory / 'state.sqlite3'
        self._mutex = threading.RLock()
        self._depth = 0
        self._lock_handle = None
        self._local = threading.local()
        if _linked(self.directory):
            raise GovernanceError('UNSAFE_METADATA', 'Governance metadata cannot be a symbolic link.')
        if create:
            from .identification import identify, require_initializable
            require_initializable(identify(self.root))
            self.root.mkdir(parents=True, exist_ok=True)
            self.directory.mkdir(exist_ok=True)
            with self.guard():
                require_initializable(identify(self.root, initializing=True))
                fresh = not self.path.exists()
                if _linked(self.path):
                    raise GovernanceError('UNSAFE_METADATA', 'The state database cannot be a symbolic link.')
                # Existing compatible databases must not be journal-migrated or
                # repaired by initialization. Upgrades are a separate action.
                if not fresh:
                    return
                with closing(sqlite3.connect(self.path, timeout=0)) as db:
                    db.execute('PRAGMA application_id=1413693785')
                    db.execute('PRAGMA journal_mode=WAL')
                    db.execute('PRAGMA synchronous=FULL')
                    db.executescript('''
                        CREATE TABLE IF NOT EXISTS records (
                            collection TEXT NOT NULL, key TEXT NOT NULL,
                            value TEXT NOT NULL, PRIMARY KEY(collection,key));
                        CREATE TABLE IF NOT EXISTS events (
                            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                            created_at TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
                    ''')
                    if fresh:
                        with db:
                            self._create_projection(db)
                            self._create_context_index(db)
        elif not self.path.is_file():
            raise GovernanceError('NOT_INITIALIZED', 'Initialize this project before using governance.')
        if _linked(self.path):
            raise GovernanceError('UNSAFE_METADATA', 'The state database cannot be a symbolic link.')

    @contextmanager
    def _connect(self, readonly=False):
        if _linked(self.directory) or _linked(self.path):
            raise GovernanceError('UNSAFE_METADATA', 'Metadata changed to a symbolic link or junction.')
        current = getattr(self._local, 'connection', None)
        if current is not None:
            # A getter inside a mutation sees that mutation's uncommitted state.
            # Only the transaction owner may commit, roll back or close it.
            yield current
            return
        mode = 'ro' if readonly else 'rw'
        connection = sqlite3.connect(self.path.as_uri() + '?mode=' + mode, uri=True, timeout=0)
        try:
            if readonly:
                connection.execute('PRAGMA query_only=ON')
                connection.execute('BEGIN')
            else:
                connection.execute('PRAGMA synchronous=FULL')
            with connection:
                yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self):
        """Atomically publish related local records and events.

        This deliberately differs from guard(): the latter protects external Git
        work whose effect journal must survive an exception. Nested transactions
        are savepoints, so a caught inner failure cannot publish partial rows.
        """
        with self.guard():
            current = getattr(self._local, 'connection', None)
            if current is not None:
                depth = getattr(self._local, 'savepoint_depth', 0) + 1
                self._local.savepoint_depth = depth
                name = 'taskcarry_' + str(depth)
                current.execute('SAVEPOINT ' + name)
                try:
                    yield self
                except BaseException:
                    current.execute('ROLLBACK TO SAVEPOINT ' + name)
                    current.execute('RELEASE SAVEPOINT ' + name)
                    raise
                else:
                    current.execute('RELEASE SAVEPOINT ' + name)
                finally:
                    self._local.savepoint_depth = depth - 1
            else:
                with self._connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    self._local.connection = db
                    try:
                        yield self
                    finally:
                        self._local.connection = None

    @contextmanager
    def guard(self):
        if not self._mutex.acquire(blocking=False):
            raise GovernanceError('BUSY', 'Another operation is changing this project; retry after it completes.')
        acquired = False
        try:
            if self._depth == 0:
                lock_path = self.directory / 'mutation.lock'
                if _linked(self.directory) or _linked(lock_path):
                    raise GovernanceError('UNSAFE_METADATA', 'The mutation guard cannot be a symbolic link.')
                self._lock_handle = open(lock_path, 'a+b')
                self._lock_handle.seek(0, os.SEEK_END)
                if self._lock_handle.tell() == 0:
                    self._lock_handle.write(b'0')
                    self._lock_handle.flush()
                self._lock_handle.seek(0)
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(self._lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(self._lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (OSError, BlockingIOError) as exc:
                    self._lock_handle.close()
                    self._lock_handle = None
                    raise GovernanceError('BUSY', 'Another process holds the project mutation guard.') from exc
            self._depth += 1
            acquired = True
            yield self
        finally:
            if acquired:
                self._depth -= 1
                if self._depth == 0 and self._lock_handle is not None:
                    try:
                        self._lock_handle.seek(0)
                        if os.name == 'nt':
                            import msvcrt
                            msvcrt.locking(self._lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(self._lock_handle, fcntl.LOCK_UN)
                    finally:
                        self._lock_handle.close()
                        self._lock_handle = None
            self._mutex.release()

    def get(self, collection, key, default=None):
        with self._connect(readonly=True) as db:
            row = db.execute('SELECT value FROM records WHERE collection=? AND key=?', (collection, key)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, collection, key, value):
        serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        with self.guard(), self._connect() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            projected = self._projection_ready(db)
            already_dirty = self._projection_dirty(db) if projected else False
            db.execute('INSERT INTO records(collection,key,value) VALUES(?,?,?) '
                       'ON CONFLICT(collection,key) DO UPDATE SET value=excluded.value',
                       (collection, key, serialized))
            if projected:
                self._project_record(db, collection, key, value)
                if not already_dirty:
                    # Clear only this write's invalidation. An older client or
                    # direct database edit must still force an explicit rebuild.
                    db.execute("UPDATE store_schema SET dirty=0 WHERE name='current_records'")
        return value

    @staticmethod
    def _projection_ready(db):
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='store_schema'").fetchone()
        if not exists:
            return False
        row = db.execute("SELECT version FROM store_schema WHERE name='current_records'").fetchone()
        if row and row[0] != CURRENT_PROJECTION_VERSION:
            raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'The current-record index requires a compatible toolkit version.')
        return row is not None

    @staticmethod
    def _projection_dirty(db):
        return bool(db.execute("SELECT dirty FROM store_schema WHERE name='current_records'").fetchone()[0])

    @staticmethod
    def _create_projection(db):
        # execute(), not executescript(): an upgrade must retain its surrounding
        # transaction, including rollback if backfilling any record fails.
        db.execute('CREATE TABLE IF NOT EXISTS store_schema (name TEXT PRIMARY KEY, version INTEGER NOT NULL, dirty INTEGER NOT NULL DEFAULT 0)')
        db.execute('''CREATE TABLE IF NOT EXISTS current_records (
            collection TEXT NOT NULL, key TEXT NOT NULL, active INTEGER NOT NULL,
            state TEXT NOT NULL, task_id TEXT, workspace TEXT, plan_id TEXT,
            PRIMARY KEY(collection,key))''')
        db.execute('CREATE INDEX IF NOT EXISTS current_records_selection ON current_records(collection,active,key)')
        db.execute("INSERT INTO store_schema(name,version) VALUES('current_records',?)",
                   (CURRENT_PROJECTION_VERSION,))
        for operation in ('INSERT', 'UPDATE', 'DELETE'):
            db.execute('CREATE TRIGGER current_records_dirty_' + operation.lower() +
                       ' AFTER ' + operation + ' ON records BEGIN '
                       "UPDATE store_schema SET dirty=1 WHERE name='current_records'; END")

    @staticmethod
    def _project_record(db, collection, key, value):
        record = value if isinstance(value, dict) else {}
        default = 'queued' if collection == 'stages' else 'pending'
        state = str(record.get('state', record.get('status', default))).lower()
        if collection in ('stages', 'operations', 'runs'):
            active = state not in TERMINAL_STATES
        elif collection == 'issues':
            active = state != 'resolved'
        elif collection == 'tasks':
            active = record.get('state') != 'complete'
        elif collection == 'artifacts':
            active = (record.get('decision') not in ('ignore', 'dismiss', 'no_backup_needed')
                      and not record.get('backup_verified'))
        else:
            active = True
        db.execute('''INSERT INTO current_records(collection,key,active,state,task_id,workspace,plan_id)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(collection,key) DO UPDATE SET
            active=excluded.active,state=excluded.state,task_id=excluded.task_id,
            workspace=excluded.workspace,plan_id=excluded.plan_id''',
                   (collection, key, int(active), state, record.get('task_id'),
                    record.get('workspace'), record.get('plan_id')))

    @staticmethod
    def _context_ready(db):
        row = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='context_schema'").fetchone()
        if not row:
            return False
        version = db.execute('SELECT version FROM context_schema').fetchone()
        if version is None or version[0] != 1:
            raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Use a compatible context index reader.')
        return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='current_records_task'").fetchone())

    @staticmethod
    def _create_context_index(db):
        db.execute('CREATE INDEX IF NOT EXISTS current_records_task ON current_records(task_id,collection,key)')
        db.execute('CREATE TABLE IF NOT EXISTS context_schema(version INTEGER NOT NULL, generation TEXT NOT NULL)')
        db.execute('DELETE FROM context_schema')
        db.execute('INSERT INTO context_schema VALUES(1,?)', (uuid.uuid4().hex,))
        db.execute('CREATE TABLE IF NOT EXISTS context_revisions(task_id TEXT PRIMARY KEY, revision INTEGER NOT NULL)')
        db.execute('DELETE FROM context_revisions')
        db.execute('CREATE TABLE IF NOT EXISTS context_record_revisions(collection TEXT NOT NULL, key TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(collection,key))')
        db.execute('DELETE FROM context_record_revisions')
        db.execute('INSERT INTO context_revisions SELECT DISTINCT task_id,1 FROM current_records WHERE task_id IS NOT NULL')
        # SQL triggers also cover compatible older clients: a reader never
        # depends on an in-memory cache or silently repairs this derived index.
        collections = "('tasks','checkpoints','observations','stages','operations','artifacts','issues','fixes','runs')"
        for operation, sources in (('insert', ('NEW',)), ('update', ('OLD', 'NEW')), ('delete', ('OLD',))):
            db.execute('DROP TRIGGER IF EXISTS context_revision_' + operation)
            statements = []
            for source in sources:
                statements.append('INSERT INTO context_record_revisions(collection,key,revision) SELECT ' + source +
                                  '.collection,' + source + '.key,1 WHERE ' + source + '.collection IN ' + collections +
                                  ' ON CONFLICT(collection,key) DO UPDATE SET revision=revision+1;')
                statements.append("INSERT INTO context_revisions(task_id,revision) SELECT json_extract(" + source +
                                  ".value,'$.task_id'),1 WHERE " + source + '.collection IN ' + collections +
                                  " AND json_type(" + source + ".value,'$.task_id')='text' "
                                  'ON CONFLICT(task_id) DO UPDATE SET revision=revision+1;')
            condition = ' WHEN OLD.value IS NOT NEW.value' if operation == 'update' else ''
            db.execute('CREATE TRIGGER context_revision_' + operation + ' AFTER ' + operation.upper() +
                       ' ON records' + condition + ' BEGIN ' + ' '.join(statements) + ' END')

    def upgrade(self):
        """Explicit, atomic index migration. Existing evidence is never rewritten."""
        with self.transaction(), self._connect() as db:
            ready = self._projection_ready(db)
            context_ready = self._context_ready(db)
            if ready and not self._projection_dirty(db) and context_ready:
                return {'upgraded': False, 'current_projection_version': CURRENT_PROJECTION_VERSION,
                        'records_rewritten': 0, 'events_rewritten': 0}
            if ready:
                db.execute('DELETE FROM current_records')
            else:
                self._create_projection(db)
            count = 0
            for collection, key, serialized in db.execute('SELECT collection,key,value FROM records ORDER BY collection,key'):
                self._project_record(db, collection, key, json.loads(serialized))
                count += 1
            db.execute("UPDATE store_schema SET dirty=0 WHERE name='current_records'")
            self._create_context_index(db)
            return {'upgraded': True, 'current_projection_version': CURRENT_PROJECTION_VERSION,
                    'indexed_records': count, 'records_rewritten': 0, 'events_rewritten': 0}

    def storage_status(self):
        with self._connect(readonly=True) as db:
            ready = self._projection_ready(db)
            dirty = self._projection_dirty(db) if ready else False
            context_ready = ready and not dirty and self._context_ready(db)
        return {'mode': 'indexed_current_v1' if ready and not dirty else 'legacy_full_scan',
                'upgrade_required': not ready or dirty, 'index_rebuild_required': dirty,
                'context_ready': context_ready, 'context_upgrade_required': not context_ready}

    def snapshot_current(self):
        """Read agenda inputs using the index, plus explicitly linked ancestors.

        This bounds history loading, not the number of genuinely current items.
        Legacy projects remain readable until the caller explicitly upgrades.
        """
        names = ('tasks', 'stages', 'operations', 'workspaces', 'artifacts',
                 'checkpoints', 'experience', 'plans', 'issues', 'runs', 'observations')
        result = {name: [] for name in names}
        with self._connect(readonly=True) as db:
            ready = self._projection_ready(db)
            dirty = self._projection_dirty(db) if ready else False
            if not ready or dirty:
                placeholders = ','.join('?' for _ in names)
                rows = db.execute('SELECT collection,value FROM records WHERE collection IN (' +
                                  placeholders + ') ORDER BY collection,key', names).fetchall()
                for collection, serialized in rows:
                    result[collection].append(json.loads(serialized))
                result['_storage'] = {'mode': 'legacy_full_scan', 'upgrade_required': True,
                                      'index_rebuild_required': dirty, 'loaded_records': len(rows)}
                return result
            loaded = 0
            for collection in ('tasks', 'stages', 'operations', 'artifacts', 'issues', 'runs'):
                rows = db.execute('''SELECT r.value FROM current_records AS c
                    JOIN records AS r ON r.collection=c.collection AND r.key=c.key
                    WHERE c.collection=? AND c.active=1 ORDER BY c.key''', (collection,)).fetchall()
                result[collection] = [json.loads(row[0]) for row in rows]
                loaded += len(rows)
            for collection in ('workspaces', 'experience'):
                rows = db.execute('SELECT value FROM records WHERE collection=? ORDER BY key', (collection,)).fetchall()
                result[collection] = [json.loads(row[0]) for row in rows]
                loaded += len(rows)
            # Unfinished runs depend on the latest receipts and observations
            # for their frozen selection, even after an effect has completed.
            for collection, id_key, reference in (('operations', 'operation_id', 'operation_ids'),
                                                   ('stages', 'stage_id', 'stage_ids'),
                                                   ('observations', 'observation_id', 'observation_ids')):
                known = {item.get(id_key) for item in result[collection]}
                for identity in sorted({key for run in result['runs'] for key in run.get(reference, [])} - known):
                    row = db.execute('SELECT value FROM records WHERE collection=? AND key=?', (collection, identity)).fetchone()
                    if row is not None:
                        result[collection].append(json.loads(row[0]))
                        loaded += 1
            stages = {item.get('stage_id'): item for item in result['stages'] if item.get('stage_id')}
            pending = [ancestor for item in result['stages'] for ancestor in item.get('supersedes', [])]
            pending.extend(item['stage_id'] for item in result['operations'] if item.get('stage_id'))
            visited = set()
            while pending:
                identity = pending.pop()
                if identity in visited:
                    continue
                visited.add(identity)
                stage = stages.get(identity)
                if stage is None:
                    row = db.execute("SELECT value FROM records WHERE collection='stages' AND key=?", (identity,)).fetchone()
                    if row is None:
                        continue
                    stage = json.loads(row[0])
                    stages[identity] = stage
                    result['stages'].append(stage)
                    loaded += 1
                pending.extend(stage.get('supersedes', []))
            for identity in sorted({item['plan_id'] for item in result['operations'] if item.get('plan_id')}):
                row = db.execute("SELECT value FROM records WHERE collection='plans' AND key=?", (identity,)).fetchone()
                if row is not None:
                    result['plans'].append(json.loads(row[0]))
                    loaded += 1
            result['stages'].sort(key=lambda item: item.get('stage_id', ''))
            result['_storage'] = {'mode': 'indexed_current_v1', 'upgrade_required': False,
                                  'index_rebuild_required': False, 'loaded_records': loaded}
            return result

    def list(self, collection):
        with self._connect(readonly=True) as db:
            rows = db.execute('SELECT value FROM records WHERE collection=? ORDER BY key', (collection,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def snapshot(self, collections):
        """Read related collections at one durable database point, without a writer lock."""
        names = tuple(dict.fromkeys(collections))
        if any(not isinstance(name, str) for name in names):
            raise ValueError('Snapshot collection names must be strings.')
        result = {name: [] for name in names}
        if not names:
            return result
        placeholders = ','.join('?' for _ in names)
        with self._connect(readonly=True) as db:
            rows = db.execute(
                'SELECT collection,value FROM records WHERE collection IN (' + placeholders + ') ORDER BY collection,key',
                names,
            ).fetchall()
        for collection, value in rows:
            result[collection].append(json.loads(value))
        return result

    def event(self, kind, payload):
        with self.guard(), self._connect() as db:
            cursor = db.execute('INSERT INTO events(created_at,kind,payload) VALUES(?,?,?)',
                                (now(), kind, json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False)))
            return cursor.lastrowid

    def events(self):
        with self._connect(readonly=True) as db:
            rows = db.execute('SELECT sequence,created_at,kind,payload FROM events ORDER BY sequence').fetchall()
        return [dict(sequence=r[0], created_at=r[1], kind=r[2], payload=json.loads(r[3])) for r in rows]
