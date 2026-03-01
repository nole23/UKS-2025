from utils.logger import UKSAuditLogger


class AuditMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        try:
            response = self.get_response(request)
            status = response.status_code

        except Exception:
            status = 500
            raise

        finally:
            user = (
                request.user.username
                if hasattr(request, "user") and request.user.is_authenticated
                else "anonymous"
            )

            UKSAuditLogger.info(
                f"{user} | {request.method} {request.path} | {response.status_code}"
            )

        return response