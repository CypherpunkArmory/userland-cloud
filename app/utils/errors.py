class JsonApiException(Exception):
    """Base exception class for unknown errors"""

    title = "Unknown error"
    status = "500"
    source = None

    def __init__(
        self,
        detail=None,
        source=None,
        title=None,
        status=None,
        code=None,
        id_=None,
        links=None,
        meta=None,
    ):
        """Initialize a jsonapi exception

        :param dict source: the source of the error
        :param str detail: the detail of the error
        """

        self.detail = detail or self.__class__.detail
        self.code = code
        self.source = source
        self.id = id_
        self.links = links or {}
        self.meta = meta or {}
        if title is not None:
            self.title = title
        if status is not None:
            self.status = status

    def to_dict(self):
        """Return values of each fields of an jsonapi error"""
        error_dict = {}
        for field in (
            "status",
            "source",
            "title",
            "detail",
            "id",
            "code",
            "links",
            "meta",
        ):
            if getattr(self, field, None):
                error_dict.update({field: getattr(self, field)})

        return error_dict


class InternalServerError(JsonApiException):
    """Raised when there is an error that can't be resolved"""

    title = "InternalServerError"
    status = "500"
    detail = "Userland Cloud has encountered an internal error - please report this at github.com/cypherpunkarmory/userland-cloud"


class BoxError(JsonApiException):
    """Raised when there is an error creating/deleting a box"""

    title = "Box Error"
    status = "500"


class ConfigError(JsonApiException):
    """Raised when there is an error creating/deleting a config"""

    title = "Config Error"
    status = "500"
    detail = "Database error when changing configs"


class UserError(JsonApiException):
    """Raised when there is an error creating/deleting a user"""

    title = "User Error"
    stats = "422"
    detail = "Database error when updating user"


class BoxLimitReached(JsonApiException):
    """Raised when the number of boxes opened is greater than the limit for their tier"""

    title = "Box Limit Reached"
    status = "403"
    detail = "Number of boxes is greater than the tier will allow"


class ConfigLimitReached(JsonApiException):
    """Raised when the number of configs reserved is greater than the limit for their tier"""

    title = "Config Limit Reached"
    status = "403"
    detail = "Number of configs is greater than the tier will allow"


class MalformedAPIHeader(JsonApiException):
    """MalformedAPIHeader error"""

    title = "Malformed api header"
    detail = (
        "`api_version` header is in the wrong format. Must be year.month.day.revision"
    )
    status = "403"


class OldAPIVersion(JsonApiException):
    """OldAPIVersion error"""

    title = "Upgrade your client"
    detail = "The client being used is incompatiable with the api"
    status = "400"


class NotFoundError(JsonApiException):
    """Raised when there is an error creating/deleting a box"""

    title = "Not Found Error"
    detail = "Not Found"
    status = "404"


class UnprocessableEntity(JsonApiException):
    """Raised when the request has the correct syntax, but is semantically incorrect"""

    title = "Unprocessable Entity"
    detail = "Unprocessable Entity"
    status = "422"


class BadRequest(JsonApiException):
    """BadRequest error"""

    title = "Bad request"
    detail = "Request does not match a known schema"
    status = "400"


class ConfigTaken(JsonApiException):
    """ConfigTaken error"""

    title = "Config Taken"
    detail = "Config has already been reserved"
    status = "400"


class ConfigInUse(JsonApiException):
    """ConfigTaken error"""

    title = "Config is being used"
    detail = "Config is associated with a running box"
    status = "403"


class AccessDenied(JsonApiException):
    """Throw this error when user does not have access"""

    title = "Access denied"
    detail = "Access denied"
    status = "403"


class UserNotConfirmed(JsonApiException):
    """Throw this error when user has not confirmed their email"""

    title = "Unconfirmed User"
    detail = "Must confirm email before you use the service"
    status = "403"


class ConsulLockException(JsonApiException):
    # Extends the base ConsulException in case caller wants to group the exception handling together
    title = "ConsulLockException"
    status = "500"


class LockAcquisitionException(JsonApiException):
    title = "LockAcquisitionException"
    status = "500"


class TooManyRequestsError(JsonApiException):
    title = "TooManyRequestsException"
    status = "429"
