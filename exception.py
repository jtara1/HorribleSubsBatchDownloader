class HorribleSubsException(Exception):
    """Raised when an exception occurs from an operation
    within HSBatchDownloader"""


class RegexFailedToMatch(HorribleSubsException):
    """One of the regex used to parse html failed to match anything"""
