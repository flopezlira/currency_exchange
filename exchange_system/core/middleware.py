import logging

from django.http import JsonResponse

# Set up a logger for the core application
logger = logging.getLogger("core")


class GlobalExceptionMiddleware:
    """
    Middleware to catch and handle all unhandled exceptions in the application.
    
    This middleware logs the exception and returns a generic error response to the client.
    """

    def __init__(self, get_response):
        """
        Initialize the middleware with the next middleware or view in the chain.
        
        :param get_response: The next middleware or view to call.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the incoming request and handle any unhandled exceptions.
        
        :param request: The HTTP request object.
        :return: The HTTP response object.
        """
        try:
            # Call the next middleware or view
            return self.get_response(request)
        except Exception as e:
            # Log the exception and return a generic error response
            logger.error(f"Unhandled exception: {e}")
            return JsonResponse(
                {"error": "An internal error occurred. Please try again later."},
                status=500,
            )
