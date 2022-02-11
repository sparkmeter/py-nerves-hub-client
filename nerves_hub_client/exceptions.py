"""NervesHub client exceptions."""


class NervesHubAPIError(BaseException):
    """Exception raised for non 200 responses."""

    def __init__(self, reason: str, status_code: int):
        """Initialize NervesHubAPIError.

        Params
        ------
        reason
            Cause of this exception
        status_code
            The HTTP status code that lead to this exception
        """
        super().__init__(reason)
        self.status_code = status_code
