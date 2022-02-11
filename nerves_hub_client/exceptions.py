"""
NervesHub client exceptions
"""


class NervesHubAPIError(BaseException):
    """Exception raised for non 200 responses"""

    def __init__(self, reason: str, status_code: int):
        super().__init__(reason)
        self.status_code = status_code
