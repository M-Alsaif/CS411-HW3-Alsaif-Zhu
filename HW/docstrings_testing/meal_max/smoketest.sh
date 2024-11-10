#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"
ECHO_JSON=false  # Set to true to display JSON output

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

# Clear all meals in the catalog
clear_meals() {
  echo "Clearing all meals..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Meals cleared successfully."
  else
    echo "Failed to clear meals."
    exit 1
  fi
}

# Create a new meal
create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Creating meal ($meal, $cuisine, $price, $difficulty)..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal created successfully."
  else
    echo "Failed to create meal."
    exit 1
  fi
}

# Delete a meal by ID
delete_meal() {
  meal_id=$1

  echo "Deleting meal with ID: $meal_id..."
  curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Meal deleted successfully."
  else
    echo "Failed to delete meal."
    exit 1
  fi
}

# Prepare a meal as a combatant
prep_combatant() {
  meal=$1

  echo "Preparing combatant: $meal..."
  curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Combatant prepared successfully."
  else
    echo "Failed to prepare combatant."
    exit 1
  fi
}

# Clear all combatants
clear_combatants() {
  echo "Clearing combatants..."
  curl -s -X POST "$BASE_URL/clear-combatants" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

# Get all combatants
get_combatants() {
  echo "Getting combatants..."
  curl -s -X GET "$BASE_URL/get-combatants" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Combatants retrieved successfully."
  else
    echo "Failed to retrieve combatants."
    exit 1
  fi
}

# Execute a battle
battle() {
  echo "Starting a battle..."
  curl -s -X GET "$BASE_URL/battle" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Battle executed successfully."
  else
    echo "Failed to execute battle."
    exit 1
  fi
}

# Get leaderboard sorted by wins
get_leaderboard() {
  echo "Getting leaderboard sorted by wins..."
  curl -s -X GET "$BASE_URL/leaderboard?sort=wins" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Leaderboard retrieved successfully."
  else
    echo "Failed to retrieve leaderboard."
    exit 1
  fi
}

# Run smoketests by calling functions in sequence
run_smoketests() {
  check_health
  check_db
  clear_meals
  clear_combatants

  # Test creating meals
  create_meal "Pasta" "Italian" 15.0 "MED"
  create_meal "Sushi" "Japanese" 20.0 "HIGH"
  create_meal "Burger" "American" 10.0 "LOW"

  # Test preparing combatants
  prep_combatant "Pasta"
  prep_combatant "Sushi"
  get_combatants

  # Test battle
  battle
  get_combatants  # Ensure only one combatant remains

  # Test leaderboard
  get_leaderboard

  # Cleanup
  clear_meals
  clear_combatants
}

# Execute smoketests
run_smoketests
