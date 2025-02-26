# Game State Representation

## Board State
The game state is represented as a concatenated vector containing:
- Board cards (level 1, 2, 3)
- Reserved cards for each player
- Permanent gems (acquired cards) for each player
- Available coins
- Noble tiles
- Current scores
- Turn information

## Action Space
Total actions = n_cards * 2 + 33 + 1
- Buy card: 0 to n_cards-1
- Reserve card: n_cards to 2*n_cards-1
- Take coins: Various combinations (wug, wur, etc.)
- Do nothing: Last action

## Game End Conditions
1. Score threshold (target_score = 1)
2. Two consecutive "do nothing" moves
3. No valid moves available

## State Management
- Main branch: Actual game state
- Branch: Used for MCTS simulations 