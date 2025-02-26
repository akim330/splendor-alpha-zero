# Neural Network Architecture

## Overview
The neural network implementation follows the AlphaZero approach with policy and value heads. The architecture is defined in `splendor/SplendorNNet.py`.

## Network Structure
- Input: Game state vector (see Game_State.md)
- Hidden Layers:
  - Dense1: 512 units with ReLU + BatchNorm + Dropout(0.3)
  - Dense2: 512 units with ReLU + BatchNorm + Dropout(0.3)
  - Dense3: 256 units with ReLU + BatchNorm
- Output Heads:
  - Policy Head: Outputs action probabilities (log softmax)
  - Value Head: Outputs state value prediction (tanh)

## Training Parameters
- Learning Rate: 0.001
- Batch Size: 64
- Epochs per Training: 10
- Loss Function:
  - Policy Loss: Cross entropy
  - Value Loss: Mean squared error 