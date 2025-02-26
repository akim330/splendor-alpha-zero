# Arena Implementation

## Overview
The Arena (`Arena.py`) manages gameplay between different versions of the AI, used primarily for model evaluation.

## Key Functions

### `playGame()`
- Manages a single game between two players
- Alternates moves between players
- Enforces game rules and tracks outcome

### `playGames(num)`
- Runs multiple evaluation games
- Tracks wins/losses/draws
- Returns performance statistics

## Usage
1. During Training
   - Evaluates new model against previous best
   - Determines if new model should be accepted

2. Model Evaluation
   - Can compare different versions
   - Useful for testing model improvements 