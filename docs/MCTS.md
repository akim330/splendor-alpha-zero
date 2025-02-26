# Monte Carlo Tree Search Implementation

## Overview
The MCTS implementation in `MCTS.py` combines traditional MCTS with neural network evaluation, following the AlphaZero approach.

## Key Components

### State Management
- `Qsa`: Q-values for state-action pairs
- `Nsa`: Visit counts for state-action pairs
- `Ns`: Visit counts for states
- `Ps`: Initial policy probabilities from neural network
- `Es`: Game ending status cache
- `Vs`: Valid moves cache

### Core Functions

#### `search(player, depth, did_nothing_last_recursion)`
- Performs one MCTS iteration
- Returns: Value of current state (-1 to 1)
- Key steps:
  1. Get canonical board state
  2. Check terminal conditions
  3. Get policy from neural network if new state
  4. Select action using UCT formula
  5. Recursively evaluate chosen action
  6. Backpropagate results

#### `getActionProb(player, temp=1)`
- Returns action probabilities after MCTS simulations
- Parameters:
  - `temp`: Temperature for exploration control
    - `temp=1`: Training mode (more exploration)
    - `temp=0`: Evaluation mode (best moves only)

### UCT Formula
Modified UCT formula for balancing exploration/exploitation:
- For visited nodes: `Q(s,a) + cpuct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))`
- For unvisited nodes: `cpuct * P(s,a) * sqrt(N(s) + 1)`

### Validation
- Policy vector size matches action space
- Policy vector sums to 1
- No NaN values in policy 