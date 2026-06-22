from backend.core.config import MediaSettings, get_media_settings


class QueueConfigurationError(Exception):
    pass


class QueueUnavailableError(Exception):
    pass


_redis_connection = None
_queue = None


def get_redis_connection(settings: MediaSettings | None = None):
    global _redis_connection
    if _redis_connection is None:
        media_settings = settings or get_media_settings()
        if not media_settings.redis_url:
            raise QueueConfigurationError("Redis is not configured.")
        try:
            from redis import Redis

            connection = Redis.from_url(media_settings.redis_url)
            connection.ping()
        except ImportError as exc:
            raise QueueConfigurationError("Redis dependency is not installed.") from exc
        except Exception as exc:
            raise QueueUnavailableError("Redis is unavailable.") from exc
        _redis_connection = connection
    return _redis_connection


def get_media_queue(settings: MediaSettings | None = None):
    global _queue
    if _queue is None:
        media_settings = settings or get_media_settings()
        try:
            from rq import Queue

            _queue = Queue(
                name=media_settings.rq_queue_name,
                connection=get_redis_connection(media_settings),
            )
        except ImportError as exc:
            raise QueueConfigurationError("RQ dependency is not installed.") from exc
        except Exception as exc:
            raise QueueUnavailableError("Redis is unavailable.") from exc
    return _queue


def reset_queue_cache() -> None:
    global _redis_connection, _queue
    try:
        if _redis_connection is not None:
            _redis_connection.close()
    except Exception:
        pass
    _redis_connection = None
    _queue = None
