import torch
import torch.nn as nn
from typing import List
from os.path import join
import os
from django.conf import settings

class MLPClassifier(torch.nn.Module):
    def __init__(self, num_classes: int = 10, hidden_sizes: List[int] = [512, 256], dropout_rate: float = 0.3):
        super().__init__()
        layers = []

        input_size = 28 * 28

        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            input_size = hidden_size
        
        layers.append(nn.Linear(input_size, num_classes))

        self.mlp_model = nn.Sequential(*layers)

    def forward(self, x):
        if len(x.shape) == 4:
            x = x.squeeze(1)

        x = x.view(x.size(0), -1)
        return self.mlp_model(x)
        

class CNNClassifier(torch.nn.Module):
    def __init__(self, num_classes: int = 10, dropout_rate: float = 0.25):
        super().__init__()

        self.cnn_model = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(dropout_rate),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(dropout_rate),
            nn.Flatten(),
            nn.Linear(128 * 7 * 7, 512),
            nn.Dropout(dropout_rate),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        # First conv block
        if len(x.shape) == 3: #(64 x 28 x 28) -> (64 x 1 x 28 x 28)
            x = x.unsqueeze(1)
    
        return self.cnn_model(x)

class LRClassifier(torch.nn.Module):
    def __init__(self, num_classes: int = 10, dropout_rate: float = 0.2):
        super().__init__()
        self.lr_model = nn.Linear(28 * 28, num_classes) 
    
    def forward(self, x):
        if len(x.shape) == 4:  # (batch_size, 1, 28, 28)
            x = x.squeeze(1)   
        
        # Flatten to (batch_size, 784)
        x = x.view(x.size(0), -1)
        
        return self.lr_model(x)
    


model_factory = {
    "mlp": MLPClassifier,
    "lr": LRClassifier,
    "cnn": CNNClassifier
}

