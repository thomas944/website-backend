import torch
import torch.nn.functional as F
import torch.nn as nn
from typing import List
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.conf import settings
import os
import base64
from PIL import Image
import io
import numpy as np
from django.conf import settings
from torchvision import transforms
import numpy as np


from .torchModels import MLPClassifier, LRClassifier, CNNClassifier

def load_models():
    mlp = MLPClassifier()
    lr = LRClassifier()
    cnn = CNNClassifier()

    base_path = os.path.join(settings.BASE_DIR, 'mnist', 'torchModels', 'models')
    mlp_path = os.path.join(base_path, 'mlp.pth')
    lr_path = os.path.join(base_path, 'lr.pth')
    cnn_path = os.path.join(base_path, 'cnn.pth')

    mlp.load_state_dict(torch.load(mlp_path, map_location=torch.device('cpu')))
    lr.load_state_dict(torch.load(lr_path, map_location=torch.device('cpu')))
    cnn.load_state_dict(torch.load(cnn_path, map_location=torch.device('cpu')))

    mlp.eval()
    lr.eval()
    cnn.eval()

    return [
        (cnn, "CNN"),
        (mlp, "MLP"),
        (lr, "LR"), 
    ]

def preprocess_image(image: Image.Image):
    transform = transforms.Compose([
        transforms.Resize((28, 28)),
        transforms.Grayscale(),
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    image = image.convert('L') 
    image_resized = image.resize((28, 28))
    image_resized.save("debug_input.png") 

    return transform(image).unsqueeze(0)

def predict_with_models(image: Image.Image, models):
    results = []
    for model, name in models:
        with torch.no_grad():
            output = model(image)
            probs = F.softmax(output, dim=1).numpy().flatten()  # Convert logits to probabilities

            all_predictions = [
                {"digit": i, "confidence": float(probs[i])}
                for i in range(10)
            ]

            top_digit = int(np.argmax(probs))
            top_prediction = {
                "digit": top_digit, 
                "confidence": float(probs[top_digit])
            }
            
            model_result = {
                "name": name,
                "output": all_predictions,
                "guess": top_prediction
            }
            results.append(model_result)
    return results
# Create your views here.


