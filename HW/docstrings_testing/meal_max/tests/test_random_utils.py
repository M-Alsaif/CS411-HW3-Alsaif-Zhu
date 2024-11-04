import pytest
import requests
from unittest.mock import patch
from meal_max.utils.random_utils import get_random

@patch("meal_max.utils.random_utils.requests.get")
def test_get_random_success(mock_get):
    """Test that a valid random number is returned when the request is successful."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "0.42"
    
    random_number = get_random()
    assert random_number == 0.42, f"Expected 0.42, but got {random_number}"


@patch("meal_max.utils.random_utils.requests.get")
def test_get_random_invalid_response(mock_get):
    """Test that a ValueError is raised when the response is not a valid float."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "invalid"

    with pytest.raises(ValueError, match="Invalid response from random.org"):
        get_random()


@patch("meal_max.utils.random_utils.requests.get")
def test_get_random_timeout(mock_get):
    """Test that a RuntimeError is raised when the request times out."""
    mock_get.side_effect = requests.exceptions.Timeout

    with pytest.raises(RuntimeError, match="Request to random.org timed out"):
        get_random()


@patch("meal_max.utils.random_utils.requests.get")
def test_get_random_request_exception(mock_get):
    """Test that a RuntimeError is raised when the request fails."""
    mock_get.side_effect = requests.exceptions.RequestException("Some error")

    with pytest.raises(RuntimeError, match="Request to random.org failed: Some error"):
        get_random()
