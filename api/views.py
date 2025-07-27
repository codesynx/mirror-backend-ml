from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import cv2
import numpy as np
from PIL import Image
import io
from .serializers import ImageUploadSerializer
import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing import image as keras_image
import requests
from django.conf import settings

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml', 'models', 'efficientnetb0_ham10000.h5')
CLASS_LABELS = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

model = None

def load_model():
    global model
    if model is None:
        model = tf.keras.models.load_model(MODEL_PATH)
    return model

@api_view(['POST'])
def predict_melanoma(request):
    """
    API endpoint for skin lesion image upload and melanoma prediction (7 classes)
    """
    serializer = ImageUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        image_file = serializer.validated_data['image']
        
        # Validate file size (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Image file size must be less than 10MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Please upload JPEG, PNG, or WebP image'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        img = Image.open(image_file).convert('RGB')
        img = img.resize((224, 224))
        img_array = np.array(img)
        img_array = preprocess_input(img_array)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Load model
        mdl = load_model()
        preds = mdl.predict(img_array)
        pred_class_idx = np.argmax(preds[0])
        pred_class = CLASS_LABELS[pred_class_idx]
        probabilities = {CLASS_LABELS[i]: float(preds[0][i]) for i in range(len(CLASS_LABELS))}
        
        response = {
            'success': True,
            'predicted_class': pred_class,
            'probabilities': probabilities,
            'message': 'This analysis is an AI-based assistant. Always consult a dermatologist for a professional diagnosis.'
        }
        return Response(response, status=status.HTTP_200_OK)
        
    except MemoryError:
        return Response(
            {'error': 'Image processing failed due to memory constraints. Please try a smaller image.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except OSError as e:
        return Response(
            {'error': 'Invalid image file. Please ensure the file is not corrupted.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error processing image: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def health_check(request):
    """
    API endpoint for service health check
    """
    return Response({
        'status': 'healthy',
        'message': 'DermAI API is active'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def chatbot(request):
    """
    Chatbot endpoint: receives 'question', returns AI response from Gemini API.
    """
    question = request.data.get('question')
    if not question:
        return Response({'error': 'Missing question.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate question length
    if len(question) > 1000:
        return Response({'error': 'Question too long. Please keep it under 1000 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        return Response({'error': 'Gemini API key not set.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": question}
                ]
            }
        ]
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        
        # Check for API errors
        if 'error' in result:
            return Response(
                {'error': f'Gemini API error: {result["error"].get("message", "Unknown error")}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Gemini response is in result['candidates'][0]['content']['parts'][0]['text']
        answer = (
            result.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', 'No answer received.')
        )
        
        if not answer or answer == 'No answer received.':
            return Response(
                {'error': 'Unable to generate response. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({'answer': answer}, status=status.HTTP_200_OK)
        
    except requests.exceptions.Timeout:
        return Response(
            {'error': 'Request timeout. Please try again.'}, 
            status=status.HTTP_408_REQUEST_TIMEOUT
        )
    except requests.exceptions.ConnectionError:
        return Response(
            {'error': 'Connection error. Please check your internet connection.'}, 
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except requests.exceptions.RequestException as e:
        return Response(
            {'error': f'Network error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Chatbot error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
