import logging

from django.core.cache import cache
from rest_framework.response import Response

from .adapters import load_adapter
from .models import ExchangeRate, Provider

logger = logging.getLogger("core")


def success_response(data, status=200):
    return Response({"success": True, "data": data}, status=status)


def error_response(error, status=400):
    return Response({"success": False, "error": error}, status=status)


