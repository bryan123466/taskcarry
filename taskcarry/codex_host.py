"""Bounded local Codex history reader. No agent turns or host mutations.

App Server itself may maintain caches/logs in the selected Codex home. This
adapter guarantees a read-method allowlist, not a zero-write host process.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

from .store import GovernanceError


TESTED_CODEX_VERSIONS = ('0.166.0-alpha.6',)
METHODS = frozenset(('initialize', 'thread/list', 'thread/read', 'thread/turns/list'))
MAX_BYTES = 2 * 1024 * 1024


def _text(value, name, maximum=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise GovernanceError('INVALID_ARGUMENT', name + ' must be bounded nonempty text.')
    return value


def _page(limit, cursor):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise GovernanceError('INVALID_ARGUMENT', 'limit must be 1-50.')
    if cursor is not None:
        _text(cursor, 'cursor', 8192)


class _Process:
    """Drain both pipes with bounded retained bytes and one total deadline."""
    def __init__(self, command, cwd, env, timeout, max_bytes):
        self.deadline = time.monotonic() + timeout
        self.max_bytes = max_bytes
        self.used = 0
        self.lock = threading.Lock()
        self.messages = queue.Queue()
        self.threads = []
        self.writers = []
        self.stderr = bytearray()
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        try:
            self.process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            creationflags=flags, shell=False)
        except OSError as exc:
            raise GovernanceError('HOST_UNAVAILABLE', 'Could not start the selected Codex executable.',
                                  {'error': str(exc)}) from exc
        for name in ('stdout', 'stderr'):
            thread = threading.Thread(target=self._drain, args=(name,), daemon=True)
            thread.start()
            self.threads.append(thread)

    def _drain(self, name):
        stream = getattr(self.process, name)
        pending = bytearray()
        try:
            while True:
                block = stream.read1(4096)
                if not block:
                    break
                with self.lock:
                    self.used += len(block)
                    if self.used > self.max_bytes:
                        self.messages.put(('error', 'HOST_OUTPUT_LIMIT'))
                        return
                if name == 'stderr':
                    self.stderr.extend(block[:max(0, 4096 - len(self.stderr))])
                    continue
                pending.extend(block)
                while b'\n' in pending:
                    line, _, pending = pending.partition(b'\n')
                    self.messages.put(('line', bytes(line)))
            if pending:
                self.messages.put(('line', bytes(pending)))
        except (OSError, ValueError):
            pass
        finally:
            self.messages.put(('eof', name))

    def receive(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise GovernanceError('HOST_TIMEOUT', 'Codex history reading exceeded its time limit.')
        try:
            kind, value = self.messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise GovernanceError('HOST_TIMEOUT', 'Codex history reading exceeded its time limit.') from exc
        if kind == 'error':
            raise GovernanceError(value, 'Codex output exceeded the configured byte limit.')
        return kind, value

    def send(self, message):
        payload = json.dumps(message).encode('utf-8') + b'\n'
        if len(payload) > self.max_bytes:
            raise GovernanceError('HOST_INPUT_LIMIT', 'Codex request exceeded the configured byte limit.')
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise GovernanceError('HOST_TIMEOUT', 'Codex history reading exceeded its time limit.')
        outcome = []
        def write():
            try:
                self.process.stdin.write(payload)
                self.process.stdin.flush()
            except (OSError, ValueError) as exc:
                outcome.append(exc)
        writer = threading.Thread(target=write, daemon=True)
        self.writers.append(writer)
        writer.start()
        writer.join(timeout=remaining)
        if writer.is_alive():
            # Closing the buffered stdin while this thread owns its lock can
            # deadlock on Windows. Termination first releases pipe backpressure.
            if self.process.poll() is None:
                self.process.kill()
            raise GovernanceError('HOST_TIMEOUT', 'Codex stopped reading input before the request deadline.')
        if outcome:
            raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex closed its input pipe.') from outcome[0]

    def close(self):
        if any(writer.is_alive() for writer in self.writers):
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait(timeout=2)
            for writer in self.writers:
                writer.join(timeout=2)
        try:
            self.process.stdin.close()
        except (OSError, ValueError):
            pass
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        for thread in self.threads:
            thread.join(timeout=2)
        self.process.stdout.close()
        self.process.stderr.close()


class CodexHost:
    def __init__(self, executable, codex_home=None, timeout=15, max_bytes=MAX_BYTES):
        path = Path(_text(executable, 'executable')).expanduser()
        if not path.is_absolute() or not path.is_file() or path.suffix.lower() in ('.cmd', '.bat', '.ps1'):
            raise GovernanceError('HOST_UNAVAILABLE', 'Select an existing absolute native Codex executable path.')
        home = Path(codex_home or os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser()
        if not home.is_absolute() or not home.is_dir():
            raise GovernanceError('HOST_UNAVAILABLE', 'Select an existing absolute Codex home directory.')
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 1 <= timeout <= 60:
            raise GovernanceError('INVALID_ARGUMENT', 'timeout must be 1-60 seconds.')
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1024 <= max_bytes <= MAX_BYTES:
            raise GovernanceError('INVALID_ARGUMENT', 'max_bytes must be 1024-2097152.')
        self.executable, self.home = path.resolve(), home.resolve()
        self.timeout, self.max_bytes = timeout, max_bytes
        self.env = dict(os.environ, CODEX_HOME=str(self.home), CODEX_SQLITE_HOME=str(self.home))

    def _version(self):
        child = _Process([str(self.executable), '--version'], self.home, self.env, self.timeout, 16384)
        try:
            output = []
            while True:
                kind, value = child.receive()
                if kind == 'eof' and value == 'stdout':
                    break
                if kind == 'line':
                    output.append(value.decode('utf-8', errors='replace'))
            value = '\n'.join(output).strip()
            version = value.removeprefix('codex-cli ')
            if version not in TESTED_CODEX_VERSIONS:
                raise GovernanceError('HOST_VERSION_UNVERIFIED', 'This Codex version has not passed the history adapter contract.',
                                      {'reported_version': value, 'tested_versions': list(TESTED_CODEX_VERSIONS),
                                       'fallback': 'Use host-provided read tools or a selected handoff.'})
            return version
        finally:
            child.close()

    @staticmethod
    def _request(child, method, params, request_id):
        if method not in METHODS:
            raise GovernanceError('HOST_METHOD_FORBIDDEN', 'Only history read methods are supported.')
        child.send({'method': method, 'id': request_id, 'params': params})
        while True:
            kind, value = child.receive()
            if kind == 'eof' and value == 'stdout':
                raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex ended before returning the requested result.',
                                      {'stderr': child.stderr.decode('utf-8', errors='replace')})
            if kind != 'line' or not value.strip():
                continue
            try:
                message = json.loads(value)
            except (ValueError, UnicodeDecodeError) as exc:
                raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex returned invalid JSON.') from exc
            if not isinstance(message, dict):
                raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex returned a non-object message.')
            if message.get('id') != request_id:
                if 'method' in message and 'id' in message:
                    raise GovernanceError('HOST_INTERACTION_REQUIRED', 'A read operation unexpectedly requested host action.',
                                          {'method': message['method']})
                continue
            if 'error' in message:
                raise GovernanceError('HOST_REQUEST_FAILED', 'The Codex history request failed.',
                                      {'method': method, 'original_error': message['error']})
            if not isinstance(message.get('result'), dict):
                raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex result must be an object.')
            return message['result']

    def _run(self, requests):
        version = self._version()
        child = _Process([str(self.executable), 'app-server', '--listen', 'stdio://'],
                         self.home, self.env, self.timeout, self.max_bytes)
        try:
            handshake = self._request(child, 'initialize', {
                'clientInfo': {'name': 'taskcarry_history_reader', 'version': '1.0.0'},
                'capabilities': {'experimentalApi': True}}, 1)
            child.send({'method': 'initialized', 'params': {}})
            results = [self._request(child, method, params, number)
                       for number, (method, params) in enumerate(requests, 2)]
            return {'source': {'kind': 'codex_local_app_server', 'executable': str(self.executable),
                               'codex_home': str(self.home), 'version': version,
                               'id': hashlib.sha256(str(self.home).encode()).hexdigest()},
                    'handshake': handshake, 'results': results, 'read_methods_only': True,
                    'agent_turn_started': False, 'host_startup_may_write_caches': True,
                    'content_is_untrusted': True,
                    'coverage': 'Selected local Codex home and its effective host configuration; a configured sqlite_home may locate its index elsewhere. No cloud or other-host completeness claim.'}
        finally:
            child.close()

    def capabilities(self):
        result = self._run([])
        result.update(methods=sorted(METHODS - {'initialize'}), state_db_only=True,
                      tested_versions=list(TESTED_CODEX_VERSIONS), history_read_verified=False)
        return result

    def list_threads(self, limit=20, cursor=None, archived=False):
        _page(limit, cursor)
        if not isinstance(archived, bool):
            raise GovernanceError('INVALID_ARGUMENT', 'archived must be boolean.')
        result = self._run([('thread/list', {'limit': limit, 'cursor': cursor, 'archived': archived,
                            'useStateDbOnly': True, 'modelProviders': [],
                            'sourceKinds': ['cli', 'vscode', 'exec', 'appServer'],
                            'sortKey': 'updated_at', 'sortDirection': 'desc'})])
        page = result.pop('results')[0]
        self._validate_page(page, limit)
        result.update(page=page, archived=archived, state_db_only=True, full_history_read=False)
        return result

    @staticmethod
    def _validate_page(page, limit):
        if not isinstance(page.get('data'), list) or len(page['data']) > limit:
            raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex returned an invalid or oversized page.')
        if page.get('nextCursor') is not None and not isinstance(page['nextCursor'], str):
            raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex returned an invalid cursor.')

    def read_thread(self, thread_id, limit=20, cursor=None):
        _text(thread_id, 'thread_id', 256)
        _page(limit, cursor)
        result = self._run([('thread/read', {'threadId': thread_id, 'includeTurns': False}),
                           ('thread/turns/list', {'threadId': thread_id, 'limit': limit, 'cursor': cursor,
                                                  'sortDirection': 'desc', 'itemsView': 'full'})])
        metadata, page = result.pop('results')
        self._validate_page(page, limit)
        if not isinstance(metadata.get('thread'), dict) or metadata['thread'].get('id') != thread_id:
            raise GovernanceError('HOST_PROTOCOL_ERROR', 'Codex returned a different thread identity.')
        result.update(thread=metadata['thread'], page=page, requested_thread_id=thread_id,
                      full_history_read=cursor is None and page.get('nextCursor') is None,
                      history_scope='Persisted turns exposed by this App Server; not unsaved or unindexed history.')
        return result


def codex_read(action, executable, codex_home=None, limit=20, cursor=None, archived=False,
               thread_id=None, timeout=15, max_bytes=MAX_BYTES):
    if action not in ('capabilities', 'list', 'read'):
        raise GovernanceError('INVALID_ARGUMENT', 'action must be capabilities, list or read.')
    host = CodexHost(executable, codex_home, timeout, max_bytes)
    if action == 'capabilities':
        return host.capabilities()
    if action == 'list':
        return host.list_threads(limit, cursor, archived)
    return host.read_thread(thread_id, limit, cursor)
