import sys
sys.path.append('..')
from utils import *

import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class SplendorNNet(nn.Module):
    def __init__(self, game, args):
        # game params
        self.input_size = game.getBoardSize()
        self.action_size = game.getActionSize()
        self.args = args

        super(SplendorNNet, self).__init__()

        self.dense1 = nn.Linear(self.input_size, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.dropout1 = nn.Dropout(0.3)
        self.dense2 = nn.Linear(512, 512)
        self.bn2 = nn.BatchNorm1d(512)
        self.dropout2 = nn.Dropout(0.3)
        self.dense3 = nn.Linear(512, 256)
        self.bn3 = nn.BatchNorm1d(256)
        
        # These two lines were missing but are used in forward()
        self.layer_to_action = nn.Linear(256, self.action_size)
        self.layer_to_value = nn.Linear(256, 1)

    def forward(self, s):
        # Add a batch dimension if it's not present
        if s.dim() == 1:
            s = s.unsqueeze(0)  # Add batch dimension
        
        s = self.bn1(F.relu(self.dense1(s)))
        s = self.dropout1(s)
        s = self.bn2(F.relu(self.dense2(s)))
        s = self.dropout2(s)
        s = self.bn3(F.relu(self.dense3(s)))
        
        pi = self.layer_to_action(s)
        v = self.layer_to_value(s)
        
        return F.log_softmax(pi, dim=1), torch.tanh(v)