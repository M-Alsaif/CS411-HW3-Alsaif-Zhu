from dataclasses import dataclass
import logging
import os
import sqlite3
from typing import Any

from meal_max.utils.sql_utils import get_db_connection
from meal_max.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Meal:
    """
    A class to manage meals.

    Attributes:
         id (int): Integer Identifier
         meal (str): String representation of meal name
         cuisine (str): String representation of cuisine 
         price (float): Float representation of the price, must be positive
         difficulty (str): String representation of difficulty chosen from a list ['LOW', 'MED', 'HIGH']

    """
    id: int
    meal: str
    cuisine: str
    price: float
    difficulty: str

    def __post_init__(self):
        """
        Initializes the meal and checks if there are any issues with the price and difficulty.
        
        Raises: 
            ValueError: If price is invalid. i.e. not a positive number.
            ValueError: If the difficulty is not part of the list ['LOW', 'MED', 'HIGH'].
        """
        if self.price < 0:
            raise ValueError("Price must be a positive value.")
        if self.difficulty not in ['LOW', 'MED', 'HIGH']:
            raise ValueError("Difficulty must be 'LOW', 'MED', or 'HIGH'.")


def create_meal(meal: str, cuisine: str, price: float, difficulty: str) -> None:
    """
    Creates a meal using inputs. 

    Args:
        meal (str): name of the meal as a string.
        cuisine (str): name of the cuisine as a string.
        price (float): price of the meal as a float.
        difficulty (str): difficulty of meal as string from the list ['LOW', 'MED', 'HIGH'].
    
    Raises: 
        ValueError: If price is invalid. i.e. not a positive number.
        ValueError: If the difficulty is not part of the list ['LOW', 'MED', 'HIGH'].
        ValueError: If a meal with the same name already exists.
        sqlite3.Error: If any database error occurs. 

    """
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError(f"Invalid price: {price}. Price must be a positive number.")
    if difficulty not in ['LOW', 'MED', 'HIGH']:
        raise ValueError(f"Invalid difficulty level: {difficulty}. Must be 'LOW', 'MED', or 'HIGH'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meals (meal, cuisine, price, difficulty)
                VALUES (?, ?, ?, ?)
            """, (meal, cuisine, price, difficulty))
            conn.commit()

            logger.info("Meal successfully added to the database: %s", meal)

    except sqlite3.IntegrityError:
        logger.error("Duplicate meal name: %s", meal)
        raise ValueError(f"Meal with name '{meal}' already exists")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def clear_meals() -> None:
    """
    Recreates the meals table, effectively deleting all meals.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_meal_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Meals cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing meals: %s", str(e))
        raise e

def delete_meal(meal_id: int) -> None:
    """
    Removes a meal using identifier (int).

    Args:
        Integer identifier of the meal: The meal to be deleted.
    
    Raises:
        ValueError: If the meal identifier is not valid.
        TypeError: If the meal is not found.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has already been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            cursor.execute("UPDATE meals SET deleted = TRUE WHERE id = ?", (meal_id,))
            conn.commit()

            logger.info("Meal with ID %s marked as deleted.", meal_id)

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_leaderboard(sort_by: str="wins") -> dict[str, Any]:
    """
    Fetches leaderboard from database.

    Args:
        sort_by parameter: The parameter to have the leaderboard be sorted through.
    
    Returns:
        leaderboard based on soft_by parameter.     

    Raises:
        ValueError: If the sort_by parameter is invalid. 
        sqlite3.Error: If any database error occurs.
    """
    query = """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.error("Invalid sort_by parameter: %s", sort_by)
        raise ValueError("Invalid sort_by parameter: %s" % sort_by)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            meal = {
                'id': row[0],
                'meal': row[1],
                'cuisine': row[2],
                'price': row[3],
                'difficulty': row[4],
                'battles': row[5],
                'wins': row[6],
                'win_pct': round(row[7] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(meal)

        logger.info("Leaderboard retrieved successfully")
        return leaderboard

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_meal_by_id(meal_id: int) -> Meal:
    """
    Retrieves a meal using identifier (id). 

    Args:
        id (int): The meal to be retrieved.
    
    Returns: 
        Meal object: The meal to be retrieved.
    
    Raises: 
        ValueError: If the meal is not found.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?", (meal_id,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
                return Meal(id=row[0], meal=row[1], cuisine=row[2], price=row[3], difficulty=row[4])
            else:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_meal_by_name(meal_name: str) -> Meal:
    """
    Retrieves a meal using name. 

    Args:
        name (str): The meal to retrieve.
    
    Returns: 
        Meal object: The meal to retrieve.
    
    Raises: 
        ValueError: If the meal is not found.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?", (meal_name,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with name %s has been deleted", meal_name)
                    raise ValueError(f"Meal with name {meal_name} has been deleted")
                return Meal(id=row[0], meal=row[1], cuisine=row[2], price=row[3], difficulty=row[4])
            else:
                logger.info("Meal with name %s not found", meal_name)
                raise ValueError(f"Meal with name {meal_name} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def update_meal_stats(meal_id: int, result: str) -> None:
    """
    Updates a meal statistics. 

    Args:
        id (int): The meal to be updated.
        "win" or "loss" (str): The result to be propagated.

    Raises: 
        ValueError: If the meal has been deleted.
        ValueError: If the result input is not "win" or "loss"
        TypeError: If the meal is not found.
        sqlite3.Error: If any database error occurs.. 
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            if result == 'win':
                cursor.execute("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?", (meal_id,))
            elif result == 'loss':
                cursor.execute("UPDATE meals SET battles = battles + 1 WHERE id = ?", (meal_id,))
            else:
                raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

            conn.commit()

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e
