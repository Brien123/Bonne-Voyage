from django.shortcuts import render
from users.models import *
from .models import *
from django.utils import timezone
from .serializers import *
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
# Create your views here.
User = get_user_model()

@api_view(['POST'])
def create_bus(request):
    try:
        user = request.user
        if user.role != User.OPERATOR:
            return Response({"error": "User not authorized to create a bus."}, status=status.HTTP_403_FORBIDDEN)

        try:
            operator = BusOperator.objects.get(user=user)
        except BusOperator.DoesNotExist:
            return Response({"error": "No corresponding BusOperator found for the user."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['operator'] = operator.id 
        
        with transaction.atomic():
            serializer = BusSerializer(data=data)
            if serializer.is_valid():
                bus = serializer.save()

                images = request.FILES.getlist('images')
                if images:
                    for image in images:
                        BusImage.objects.create(bus=bus, image=image)
                        
                route = Route.objects.create(
                    bus=bus,
                    origin=data['origin'],
                    destination=data['destination'],
                    distance=data['distance']
                )
                
                schedule = Schedule.objects.create(
                    bus=bus,
                    route=route,
                    departure_time=data['departure_time'],
                    arrival_time=data['arrival_time'],
                    price=data['price'],
                    currency='XAF'
                )
                
                response_data = {
                    "message": "Bus successfully created",
                    "Bus": BusSerializer(bus).data
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_schedule(request):
    try:
        user = request.user

        if user.role != User.OPERATOR:
            return Response({"error": "User not authorized to create a schedule."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            operator = BusOperator.objects.get(user=user)
        except BusOperator.DoesNotExist:
            return Response({"error": "No corresponding BusOperator found for the user."}, status=status.HTTP_400_BAD_REQUEST)

        bus_id = request.data.get('bus_id')
        try:
            bus = Bus.objects.get(id=bus_id, operator=operator)
        except Bus.DoesNotExist:
            return Response({"error": "No bus found for this operator with the provided ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['bus'] = bus.id 
        data['route'] = data['route_id']

        serializer = ScheduleCreateSerializer(data=data)
        if serializer.is_valid():
            schedule = serializer.save()
            response_data = {
                "message": "Schedule created successfully!",
                "schedule": ScheduleCreateSerializer(schedule).data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# @api_view(["POST"])
# def create(request):
#     user = request.user
#     if user.role != User.OPERATOR:
#         return Response({"error": "User not authorized to create a schedule."}, status=status.HTTP_403_FORBIDDEN)
        
#     try:
#         data = request.data
#         operator = BusOperator.objects.get(user=user)
        
#         with transaction.atomic():
#             Bus.objects.create(
#                 operator=operator,
#                 name=data['name'],
#                 bus_number=data['bus_number'],
#                 capacity=data['capacity'],
#                 amenities=data['amenities']
#             )
#             images = request.FILES.getlist('images')
#             if images:
#                 for image in images:
#                     BusImage.objects.create(bus=bus, image=image)
@api_view(['GET'])
def buses(request):
    try:
        buses = Bus.objects.all().order_by('created_at')
        buses_data = []

        for bus in buses:
            bus_data = BusSerializer(bus).data

            bus_images = BusImage.objects.filter(bus=bus)
            bus_data['images'] = [image.image.url for image in bus_images]

            bus_routes = Route.objects.filter(bus=bus)
            bus_data['routes'] = RouteSerializer(bus_routes, many=True).data

            bus_schedules = Schedule.objects.filter(bus=bus)
            bus_data['schedules'] = ScheduleSerializer(bus_schedules, many=True).data

            buses_data.append(bus_data)

        return Response(buses_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def bus_detail_view(request, id):
    try:
        with transaction.atomic():
            bus = Bus.objects.get(id=id)

            bus_images = BusImage.objects.filter(bus=bus)
            bus_route = Route.objects.filter(bus=bus).first() 
            bus_schedule = Schedule.objects.filter(bus=bus)

        bus_data = {
            'bus': BusSerializer(bus).data,
            'images': [image.image.url for image in bus_images],
            'route': RouteSerializer(bus_route).data if bus_route else None,
            'schedule': ScheduleSerializer(bus_schedule, many=True).data
        }
        return Response(bus_data, status=status.HTTP_200_OK)
        
    except Bus.DoesNotExist:
        return Response({"error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# @api_view(['POST'])
# def book(request):
#     user = rquest.user
    
#     try:
        

        
    
    
        
