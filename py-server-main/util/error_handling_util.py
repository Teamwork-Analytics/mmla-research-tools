import logging
from typing import Tuple

from util.validation_util import validate_string_argument, validate_http_status_code


def build_error_response(error_message: str, status_code: int) -> tuple[str, int]:
    """
        Constructs an error response with the provided error message and HTTP status code.

        This function validates that `error_message` is a non-empty string and `status_code`
        is a valid HTTP status code. It logs the error message for tracking purposes.

        Args:
            error_message (str): The error message to include in the response.
            status_code (int): The HTTP status code for the error response.

        Returns:
            tuple[str, int]: A tuple containing the error message and status code.

        Raises:
            ValueError: If `error_message` is not a valid string or `status_code` is not a
                        valid HTTP status code.
        """
    validate_string_argument(error_message)
    validate_http_status_code(status_code)
    logging.info(f"{error_message}")
    return error_message, status_code
