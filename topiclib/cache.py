from abc import ABC, abstractclassmethod
from multiprocessing import Lock
import sqlite3

cachenames = {}

# Abstract caching class
class ICache(ABC):
    @abstractclassmethod
    def get(self, key: str) -> str:
        pass

    @abstractclassmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractclassmethod
    def delete(self, key: str) -> None:
        pass

    @abstractclassmethod
    def clear(self) -> None:
        pass

    @abstractclassmethod
    def keys(self) -> [str]:
        pass

    @abstractclassmethod
    def values(self) -> [str]:
        pass

    @abstractclassmethod
    def items(self) -> [(str, str)]:
        pass

    @abstractclassmethod
    def __contains__(self, key: str) -> bool:
        pass

    @abstractclassmethod
    def __len__(self) -> int:
        pass

    @abstractclassmethod
    def __iter__(self) -> iter:
        pass

    @abstractclassmethod
    def __getitem__(self, key: str) -> str:
        pass

    @abstractclassmethod
    def __setitem__(self, key: str, value: str) -> None:
        pass

    @abstractclassmethod
    def __delitem__(self, key: str) -> None:
        pass

    def set_lock(self, lock: Lock) -> None:
        self._lock = lock


def synchronized_method(func):
    """Checks for self._lock and wraps the method with the mutex."""
    def _synchronized(self, *args, **kw):
        if not hasattr(self, "_lock"):
            raise Exception("No lock found (self._lock must be defined)")
        with self._lock:
            return func(self, *args, **kw)
    return _synchronized


def cacheclass(init):
    """Decorator for adding more cache classes. This should wrap the init method"""
    def _wraped_init(self, *args, **kwargs):
        cls = type(self)
        assert issubclass(cls, ICache)
        cachenames[cls.__name__] = cls
        init(self, *args, **kwargs)

    return _wraped_init

class SqliteCache(ICache):
    """sqlite file cache"""

    @cacheclass
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
        self._lock = Lock()

    @synchronized_method
    def get(self, key: str) -> str:
        cursor = self.conn.execute(
            "SELECT value FROM cache WHERE key=?", (key,))
        row = cursor.fetchone()
        if row is None:
            return None
        cursor.close()
        return row[0]

    @synchronized_method
    def set(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    @synchronized_method
    def delete(self, key: str) -> None:
        self.conn.execute("DELETE FROM cache WHERE key=?", (key,))
        self.conn.commit()

    @synchronized_method
    def clear(self) -> None:
        self.conn.execute("DELETE FROM cache")
        self.conn.commit()
        self.conn.execute("VACUUM")
        self.conn.commit()

    @synchronized_method
    def keys(self) -> [str]:
        cursor = self.conn.execute("SELECT key FROM cache")
        rows = [row[0] for row in cursor]
        cursor.close()
        return rows

    @synchronized_method
    def values(self) -> [str]:
        cursor = self.conn.execute("SELECT value FROM cache")
        rows = [row[0] for row in cursor]
        cursor.close()
        return rows

    @synchronized_method
    def items(self) -> [(str, str)]:
        cursor = self.conn.execute("SELECT key, value FROM cache")
        rows = [(row[0], row[1]) for row in cursor]
        cursor.close()
        return rows

    @synchronized_method
    def __contains__(self, key: str) -> bool:
        cursor = self.conn.execute("SELECT key FROM cache WHERE key=?", (key,))
        contains = cursor.fetchone() is not None
        cursor.close()
        return contains

    @synchronized_method
    def __len__(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM cache")
        node = cursor.fetchone()[0]
        cursor.close()
        return node

    @synchronized_method
    def __iter__(self) -> iter:
        cursor = self.conn.execute("SELECT key FROM cache")
        rows = (row[0] for row in cursor)
        cursor.close()
        return rows

    def __getitem__(self, key: str) -> str:
        return self.get(key)

    def __setitem__(self, key: str, value: str) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        self.delete(key)


class Singleton(object):
    """Singleton metaclass"""
    _instances = {}

    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(
                Singleton, class_).__new__(class_, *args, **kwargs)
        return class_._instances[class_]


class Cache(Singleton):
    """Singleton that stores globally set cache instance"""
    _cache: ICache = None

    @classmethod
    def instance(cls) -> ICache:
        if cls._cache is None:
            raise Exception("Cache not set")
        return cls._cache

    @classmethod
    def set_cache(cls, cache: ICache):
        if not issubclass(type(cache), ICache):
            raise Exception("Cache must be an instance of ICache")
        cls._cache = cache

