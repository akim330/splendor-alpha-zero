# Training Process

## Overview
The training process is managed by the Coach class in `Coach.py`, which implements the AlphaZero training loop.

## Training Loop
1. Self-Play Phase
   - Generates training examples through MCTS-guided gameplay
   - Uses temperature parameter for exploration
   - Stores game states, policies, and outcomes

2. Neural Network Training
   - Trains on examples from recent self-play games
   - Updates network weights to better predict:
     - Action probabilities (policy)
     - Game outcomes (value)

3. Model Evaluation
   - New model plays against previous best
   - If win rate > threshold, new model is accepted
   - Maintains best model checkpoint

## Key Parameters
- Number of self-play games per iteration
- MCTS simulations per move
- Temperature schedule for exploration
- Training examples history size
- Arena evaluation games count
- Update acceptance threshold

## Logging
- Clears log file every 5000 writes
- Tracks:
  - Training progress
  - Game outcomes
  - Model evaluation results
  - MCTS statistics 