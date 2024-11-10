from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal, 
    create_meal, 
    clear_meals, 
    delete_meal, 
    get_meal_by_id, 
    get_leaderboard, 
    get_meal_by_name,
    update_meal_stats
    )

######################################################
#
#    Fixtures
#
######################################################
def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################
def test_create_meal(mock_cursor):
    """Test creating a new meal in the kitchen."""

    # Call the function to create a new meal
    create_meal(meal="Meal name", cuisine="Cuisine Name", price=2.99, difficulty="LOW")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal name", "Cuisine Name", 2.99, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a song with a duplicate meal."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: Meal.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(meal="Meal Name", cuisine="Cuisine Name", price=2.99, difficulty="LOW")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative price)"""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -2.99. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine Name", price=-2.99, difficulty="LOW")


def test_delete_meal(mock_cursor):
    """Test soft deleting a song from the kitchen by Meal ID."""

    # Simulate that the song exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_song function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing the entire kitchen meals (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()
    
######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Name", 2.99, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Name", 2.99, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_song_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_song_by_id_deleted(mock_cursor):
    # Simulate that a deleted meal exists for the given ID
    mock_cursor.fetchone.return_value = [999, "Meal Name", "Cuisine Name", 3.99, "LOW", True]

    # Expect a ValueError when the meal the deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        get_meal_by_id(999)


def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists id = 1, meal = "Meal Name", cuisine = "Cuisine Name", price = 2.99, difficulty = "LOW",
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Name", 2.99, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Name", 2.99, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ('Meal Name',)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_name_deleted(mock_cursor):
    # Simulate that a deleted meal exists for the given Meal name
    mock_cursor.fetchone.return_value = [1, "Meal Name", "Cuisine Name", 3.99, "LOW", True]

    # Expect a ValueError when the meal is deleted
    with pytest.raises(ValueError, match="Meal with name Meal Name has been deleted"):
        get_meal_by_name("Meal Name")
    
def test_get_meal_by_name_bad_name(mock_cursor):
    # Simulate that no meal exists for the given Meal name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name Meal Name not found"):
        get_meal_by_name("Meal Name")


##################################################
# Update Statistics
##################################################
def test_update_meal_stats_win(mock_cursor):
    """Test updating the stats of a meal (win)."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID
    result = "win"
    meal_id = 1
    update_meal_stats(meal_id, result)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (song ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_loss(mock_cursor):
    """Test updating the stats of a meal (loss)."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID
    result = "loss"
    meal_id = 1
    update_meal_stats(meal_id, result)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (song ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_invalid(mock_cursor):
    """Test updating the stats of a meal (invalid)."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID
    result = "tie"
    meal_id = 1
    # Expect a ValueError when attempting to update a meal with invalid result
    with pytest.raises(ValueError, match="Invalid result: tie. Expected 'win' or 'loss'."):
        update_meal_stats(meal_id, result)

### Test for Updating a Deleted Meal:
def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update meal stats for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

    # Ensure that no SQL query for updating play count was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))


##################################################
# Get Leaderboard
##################################################

def test_get_leaderboard_win_para(mock_cursor):
    """Test retrieving leaderboard using win parameter."""

    # Simulate that there are multiple songs in the database
    mock_cursor.fetchall.return_value = [
        (2, "Artist B", "Song B", 2021, "Pop", 180, 20),
        (1, "Artist A", "Song A", 2020, "Rock", 210, 10),
        (3, "Artist C", "Song C", 2022, "Jazz", 200, 5)
    ]

    # Call the get_all_songs function with sort_by_play_count = True
    songs = get_all_songs(sort_by_play_count=True)

    # Ensure the results are sorted by play count
    expected_result = [
        {"id": 2, "artist": "Artist B", "title": "Song B", "year": 2021, "genre": "Pop", "duration": 180, "play_count": 20},
        {"id": 1, "artist": "Artist A", "title": "Song A", "year": 2020, "genre": "Rock", "duration": 210, "play_count": 10},
        {"id": 3, "artist": "Artist C", "title": "Song C", "year": 2022, "genre": "Jazz", "duration": 200, "play_count": 5}
    ]

    assert songs == expected_result, f"Expected {expected_result}, but got {songs}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, artist, title, year, genre, duration, play_count
        FROM songs
        WHERE deleted = FALSE
        ORDER BY play_count DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_winpct_sortby_para(mock_cursor):


def test_get_leaderboard_invalid_sortby_para(mock_cursor):