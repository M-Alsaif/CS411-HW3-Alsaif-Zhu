import pytest
from unittest.mock import patch, MagicMock
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()


@pytest.fixture
def sample_meal1():
    return Meal(id=1, meal='Meal 1', cuisine='Chinese', price=20.0, difficulty='MED')


@pytest.fixture
def sample_meal2():
    return Meal(id=2, meal='Meal 2', cuisine='Ecuadorian', price=25.0, difficulty='LOW')


##################################################
# Battle Management Test Cases
##################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a combatant to the battle."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == 'Meal 1'


def test_prep_combatant_full(battle_model, sample_meal1, sample_meal2):
    """Test adding a combatant when there are already two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    with pytest.raises(ValueError, match="Combatant list is full"):
        battle_model.prep_combatant(sample_meal1)


def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
    """Test clearing the combatants list."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    assert len(battle_model.combatants) == 2

    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0


##################################################
# Battle Execution Test Cases
##################################################

def test_battle_no_combatants(battle_model):
    """Test battle with no combatants raises an error."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle"):
        battle_model.battle()


def test_battle_one_combatant(battle_model, sample_meal1):
    """Test battle with only one combatant raises an error."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle"):
        battle_model.battle()


@patch("meal_max.models.battle_model.get_random")
@patch("meal_max.models.battle_model.update_meal_stats")
def test_battle_with_two_combatants(mock_update_stats, mock_get_random, battle_model, sample_meal1, sample_meal2):
    """Test a battle between two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    mock_get_random.return_value = 0.5

    winner_name = battle_model.battle()

    # Verify correct combatant is removed
    assert len(battle_model.combatants) == 1
    assert winner_name in [sample_meal1.meal, sample_meal2.meal]

    # Check update_meal_stats was called for both meals
    mock_update_stats.assert_any_call(sample_meal1.id, 'win')
    mock_update_stats.assert_any_call(sample_meal2.id, 'loss')



##################################################
# Battle Score Calculation Test Cases
##################################################

def test_get_battle_score_medium_difficulty(battle_model, sample_meal1):
    """Test score calculation with MEDIUM difficulty."""
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 2
    assert score == expected_score, f"Expected score {expected_score}, got {score}"


def test_get_battle_score_low_difficulty(battle_model, sample_meal2):
    """Test score calculation with LOW difficulty."""
    score = battle_model.get_battle_score(sample_meal2)
    expected_score = (sample_meal2.price * len(sample_meal2.cuisine)) - 3
    assert score == expected_score, f"Expected score {expected_score}, got {score}"


def test_get_battle_score_high_difficulty(battle_model):
    """Test score calculation with HIGH difficulty."""
    meal = Meal(id=3, meal='Meal 3', cuisine='Korean', price=30.0, difficulty='HIGH')
    score = battle_model.get_battle_score(meal)
    expected_score = (meal.price * len(meal.cuisine)) - 1
    assert score == expected_score, f"Expected score {expected_score}, got {score}"
def test_get_battle_score_low_difficulty_high_price(battle_model):
    """Test score calculation with LOW difficulty and high price."""
    meal = Meal(id=4, meal='Meal 4', cuisine='Mexican', price=100.0, difficulty='LOW')
    score = battle_model.get_battle_score(meal)
    expected_score = (meal.price * len(meal.cuisine)) - 3
    assert score == expected_score, f"Expected score {expected_score}, got {score}"


def test_get_battle_score_medium_difficulty_low_price(battle_model):
    """Test score calculation with MEDIUM difficulty and low price."""
    meal = Meal(id=5, meal='Meal 5', cuisine='Italian', price=5.0, difficulty='MED')
    score = battle_model.get_battle_score(meal)
    expected_score = (meal.price * len(meal.cuisine)) - 2
    assert score == expected_score, f"Expected score {expected_score}, got {score}"


def test_get_battle_score_high_difficulty_zero_price(battle_model):
    """Test score calculation with HIGH difficulty and zero price."""
    meal = Meal(id=6, meal='Meal 6', cuisine='Japanese', price=0.0, difficulty='HIGH')
    score = battle_model.get_battle_score(meal)
    expected_score = (meal.price * len(meal.cuisine)) - 1
    assert score == expected_score, f"Expected score {expected_score}, got {score}"


def test_get_battle_score_varied_difficulty_and_price(battle_model):
    """Test score calculation with various difficulties and prices."""
    test_cases = [
        {"meal": Meal(id=7, meal='Meal 7', cuisine='French', price=50.0, difficulty='LOW'), "expected_modifier": 3},
        {"meal": Meal(id=8, meal='Meal 8', cuisine='Thai', price=10.0, difficulty='MED'), "expected_modifier": 2},
        {"meal": Meal(id=9, meal='Meal 9', cuisine='Indian', price=40.0, difficulty='HIGH'), "expected_modifier": 1},
    ]

    for case in test_cases:
        meal = case["meal"]
        expected_score = (meal.price * len(meal.cuisine)) - case["expected_modifier"]
        score = battle_model.get_battle_score(meal)
        assert score == expected_score, f"Expected score {expected_score} for {meal.meal}, got {score}"


##################################################
# Combatant Retrieval Test Cases
##################################################

def test_get_combatants(battle_model, sample_meal1, sample_meal2):
    """Test retrieving the list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    combatants = battle_model.get_combatants()
    assert len(combatants) == 2
    assert combatants[0].meal == 'Meal 1'
    assert combatants[1].meal == 'Meal 2'

def test_get_combatants_no_combatants(battle_model):
    """Test retrieving the list of combatants when there are no combatants."""
    combatants = battle_model.get_combatants()
    assert len(combatants) == 0, "Expected no combatants in the list"


def test_get_combatants_one_combatant(battle_model, sample_meal1):
    """Test retrieving the list of combatants when there is only one combatant."""
    battle_model.prep_combatant(sample_meal1)
    combatants = battle_model.get_combatants()
    assert len(combatants) == 1
    assert combatants[0].meal == 'Meal 1'


def test_get_combatants_more_than_two(battle_model, sample_meal1, sample_meal2):
    """Test that adding more than two combatants raises an error and only retains the first two."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    
    with pytest.raises(ValueError, match="Combatant list is full"):
        extra_meal = Meal(id=3, meal='Meal 3', cuisine='French', price=15.0, difficulty='LOW')
        battle_model.prep_combatant(extra_meal)

    combatants = battle_model.get_combatants()
    assert len(combatants) == 2
    assert combatants[0].meal == 'Meal 1'
    assert combatants[1].meal == 'Meal 2'
