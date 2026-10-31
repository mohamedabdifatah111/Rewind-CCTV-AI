try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except ImportError:  # celery is optional in sync/thread modes
    pass
