# Splendor Alpha Zero

This project implements an Alpha Zero approach to learning the board game Splendor. It uses Monte Carlo Tree Search (MCTS) combined with deep learning to learn gameplay strategies through self-play.

## Project Structure

- `main.py` - Entry point for training and evaluation
- `Coach.py` - Handles the self-play training loop and neural network updates
- `MCTS.py` - Implements Monte Carlo Tree Search algorithm
- `Arena.py` - Manages gameplay between different versions of the AI
- `splendor/` - Core game implementation and neural network architecture
  - `SplendorGame.py` - Implements game rules and state management
  - `SplendorNNet.py` - Neural network architecture
  - `NNet.py` - Neural network training and inference wrapper
  - `config.py` - Game configuration (cards, nobles, etc.)
  - `configs/` - Different game variants/configurations
  - `variants/` - Game variant implementations

## Key Components

### Game Rules
- Target score is 1 point
- Game ends when either:
  - A player reaches target score (checked at end of player 2's turn)
  - Two consecutive "do nothing" moves
  - No valid moves available

### Neural Network
- Input: Game state representation
- Outputs:
  - Policy head (action probabilities)
  - Value head (game state evaluation)

### MCTS
- Uses UCT formula for action selection
- Combines neural network evaluation with tree search
- Validates policy vectors for size and probability distribution

## Training Process

1. Self-play games generate training examples
2. Neural network trains on these examples
3. New network version competes against previous version
4. If new version performs better, it becomes the current best

## Recent Changes

- Implemented log rotation to manage log file size
- Modified UCT formula for unvisited nodes
- Added policy vector validation in MCTS

## Usage

[To be added: Instructions for running training, evaluation, etc.]
