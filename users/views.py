from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, BusOperatorSerializer, ChangePasswordSerializer
from django.db import transaction
from .models import *
from buses.serializers import *
from django.contrib.auth import logout as django_logout

User = get_user_model()

@api_view(['POST'])
def register_view(request):
    try:
        serializer = RegisterSerializer(data=request.data)
        with transaction.atomic():
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)

                if user.role == User.OPERATOR:
                    images = request.FILES.getlist('images')
                    if images:
                        for image in images:
                            operator = BusOperator.objects.get(user=user)
                            BusOperatorImage.objects.create(operator=operator, image=image)
                    
                response_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login_view(request):
    try:
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return f"error: {e}"
 
@api_view(['POST'])
def logout(request):
    try:
        django_logout(request)
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
@api_view(['POST'])
def edit_operator_profile(request):
    user = request.user
    if user.role != User.OPERATOR:
        return Response({"error": "User not authorized to edit profile."}, status=status.HTTP_403_FORBIDDEN)

    try:
        operator = BusOperator.objects.get(user=user)
    except BusOperator.DoesNotExist:
        return Response({"error": "No corresponding BusOperator found for the user."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = BusOperatorSerializer(operator, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': "Profile successfully updated.",
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_password(request):
    try:
        user = request.user
        serializer = ChangePasswordSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': "Password successfully updated.",
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
