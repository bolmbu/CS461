import json
import sqlite3
import time
import uuid
from pathlib import Path
from contextlib import contextmanager
from threading import Lock, RLock
from weakref import WeakValueDictionary


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._locks = WeakValueDictionary()
        self._locks_guard = Lock()
        self.path = self.directory / 'coopready.sqlite3'
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, updated REAL NOT NULL)')

    @contextmanager
    def session_lock(self, sid):
        with self._locks_guard:
            lock = self._locks.get(sid)
            if lock is None:
                lock = RLock()
                self._locks[sid] = lock
        with lock:
            yield

    def connect(self):
        return sqlite3.connect(self.path, timeout=20)

    def put(self, kind, payload, record_id=None):
        record_id = record_id or str(uuid.uuid4())
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO records VALUES (?, ?, ?, ?)', (record_id, kind, json.dumps(payload, ensure_ascii=False), time.time()))
        return record_id

    def get(self, record_id, kind):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM records WHERE id=? AND kind=?', (record_id, kind)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, kind):
        with self.connect() as db:
            rows = db.execute('SELECT id,payload,updated FROM records WHERE kind=? ORDER BY updated DESC', (kind,)).fetchall()
        return [dict(id=r[0], data=json.loads(r[1]), updated=r[2]) for r in rows]

    def delete(self, record_id):
        with self.connect() as db:
            db.execute('DELETE FROM records WHERE id=?', (record_id,))

    def purge(self, days):
        with self.connect() as db:
            cur = db.execute("DELETE FROM records WHERE kind!='faq' AND updated<?", (time.time()-days*86400,))
        # Audio uses the same configured retention, including temporary downloads.
        for p in self.directory.glob('*.wav'):
            if p.stat().st_mtime < time.time()-days*86400:
                p.unlink(missing_ok=True)
        return cur.rowcount
