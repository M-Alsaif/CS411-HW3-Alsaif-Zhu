#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

###############################################
# Health Checks
###############################################

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

###############################################
# Meal Management Tests
###############################################

# Clear meals table
clear_meals() {
  echo "Clearing all meals..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "All meals cleared successfully."
  else
    echo "Failed to clear meals."
    exit 1
  fi
}

# Test meal creation
create_meal_test() {
  meal_name="$1"
  cuisine="$2"
  price="$3"
  difficulty="$4"
  
  echo "Creating meal: $meal_name, Cuisine: $cuisine, Price: $price, Difficulty: $difficulty"
  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal_name\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal created successfully."
  else
    echo "Failed to create meal."
    exit 1
  fi
}

# Test fetching meal by ID
get_meal_by_id_test() {
  local meal_id="$1"
  
  echo "Fetching meal by ID: $meal_id"
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID."
  else
    echo "Failed to retrieve meal by ID."
    exit 1
  fi
}

# Test deleting meal by ID
delete_meal_test() {
  meal_id="$1"
  echo "Deleting meal by ID: $meal_id"
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully."
  else
    echo "Failed to delete meal."
    exit 1
  fi
}

###############################################
# Combatant Management
###############################################

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

###############################################
# Battle Simulation
###############################################

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

###############################################
# Run Tests in Sequence
###############################################

clear_meals
check_health
check_db
clear_meals
clear_combatants

# Test creating meals
create_meal_test "Pasta" "Italian" 15.0 "MED"
create_meal_test "Sushi" "Japanese" 20.0 "HIGH"
create_meal_test "Burger" "American" 10.0 "LOW"

# Test preparing combatants
prep_combatant "Pasta"
prep_combatant "Sushi"
get_combatants

# Test battle
battle
get_combatants # Ensure only one combatant remains

# Test leaderboard
get_leaderboard

# Cleanup
clear_meals
clear_combatants

# Run meal creation test
create_meal_test "Pasta" "Italian" 15.99 "MED"
get_meal_by_id_test 1
delete_meal_test 1
create_meal_test "Sushi" "Japanese" 20.0 "HIGH"
create_meal_test "Burger" "American" 10.5 "LOW"
get_meal_by_id_test 2
delete_meal_test 3
get_meal_by_id_test 2

# Run leaderboard test sorted by wins
get_leaderboard 

echo "All tests completed successfully."
