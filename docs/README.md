# Splendor Alpha Zero Documentation

## Core Components and Their Interactions

### Game Implementation (`splendor/`)
- `SplendorGame.py`: Core game logic and state management
- `config.py`: Game configuration (cards, nobles)
- `configs/simple.py`: Simplified game variant

### Learning Components
1. **MCTS** (`MCTS.py`)
   - Uses neural network for state evaluation
   - Guides action selection during gameplay
   - See [MCTS.md](MCTS.md)

2. **Neural Network** (`splendor/SplendorNNet.py`, `splendor/NNet.py`)
   - Evaluates game states
   - Provides action probabilities
   - See [Neural_Network.md](Neural_Network.md)

3. **Training Process** (`Coach.py`)
   - Manages self-play and learning loop
   - Coordinates MCTS and neural network
   - See [Training_Process.md](Training_Process.md)

4. **Game State** (`splendor/SplendorGame.py`)
   - Represents and manages game state
   - Handles game rules and valid moves
   - See [Game_State.md](Game_State.md)

### Entry Points
- `main.py`: Training and evaluation entry point
- `Arena.py`: Model comparison framework

## Component Interaction Flow
1. Coach initiates self-play games
2. MCTS uses neural network to guide move selection
3. Game states and outcomes recorded as training examples
4. Neural network trains on collected examples
5. Arena evaluates improved neural network
6. Cycle repeats with better model 