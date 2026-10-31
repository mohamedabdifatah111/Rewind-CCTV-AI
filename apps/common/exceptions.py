import logging
from rest_framework.response import Response
from rest_framework.views import exception_handler
logger = logging.getLogger(__name__)

def api_exception_handler(exc, context):
    """DRF errors keep their shape; anything unexpected becomes a generic 500 with no internals."""
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled error in %s", context.get("view").__class__.__name__)
        return Response({"detail": "Internal server error."}, status=500)
    return response
