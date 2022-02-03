class NervesHubAPIError(BaseException):
    """Exception raised for non 200 responses"""

    def __init__(self, status_code: int, reason: str):
        self.status_code = status_code
        self.reason = reason
