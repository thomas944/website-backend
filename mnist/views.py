from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
import base64
import io

from .torchModels.utils import load_models, predict_with_models, preprocess_image

models = load_models()

@api_view(['POST'])
@parser_classes([JSONParser])
def predict(request):
    try:
        base64_image = request.data.get('image')
        if not base64_image:
            return Response({"error": "Image data not provided."}, status=status.HTTP_400_BAD_REQUEST)

        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        input_tensor = preprocess_image(image)
        predictions = predict_with_models(input_tensor, models)

        return Response(predictions)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(['GET'])
def testing(request):
    return Response({'success': True})


@api_view(['GET'])
def index(request):
    return Response({'message': 'Server is running...'})