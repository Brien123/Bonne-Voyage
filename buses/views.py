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
from .tasks import initiate_payment_task, disburse
from django.shortcuts import get_object_or_404
from campay.sdk import Client as CamPayClient
from dotenv import load_dotenv
from django.db.models import Sum
import time
import os
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from users.serializers import *

# Create your views here.
User = get_user_model()

campay = CamPayClient({
    "app_username": os.getenv('CAMPAY_USERNAME'),
    "app_password": os.getenv('CAMPAY_PASSWORD'),
    "environment": "DEV"
})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the bus'),
            'bus_number': openapi.Schema(type=openapi.TYPE_STRING, description='Bus registration number'),
            'capacity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Capacity of the bus'),
            'amenities': openapi.Schema(type=openapi.TYPE_STRING, description='Amenities provided in the bus'),
            'origin': openapi.Schema(type=openapi.TYPE_STRING, description='Route origin'),
            'destination': openapi.Schema(type=openapi.TYPE_STRING, description='Route destination'),
            'distance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Distance of the route'),
            'departure_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Departure time of the schedule'),
            'arrival_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Arrival time of the schedule'),
            'price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Price of the schedule'),
            'images': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_FILE), description='Images of the bus'),
        }
    ),
    responses={
        201: openapi.Response('Created', BusSerializer),
        400: "Bad Request",
        403: "Forbidden",
        500: "Internal Server Error"
    },
    operation_description="Create a new bus. Only accessible to users with the 'OPERATOR' role."
)
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


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['bus_id', 'route_id', 'departure_time', 'arrival_time', 'price'],
        properties={
            'bus_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bus'),
            'route_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the route'),
            'departure_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Departure time of the schedule'),
            'arrival_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Arrival time of the schedule'),
            'price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Price of the schedule')
        }
    ),
    responses={
        201: openapi.Response('Created', ScheduleCreateSerializer),
        400: "Bad Request",
        403: "Forbidden",
        500: "Internal Server Error"
    },
    operation_description="Create a new schedule for a bus. Only accessible to users with the 'OPERATOR' role."
)
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
 
    
@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bus'),
                        'operator': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the operator'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the bus'),
                        'bus_number': openapi.Schema(type=openapi.TYPE_STRING, description='Bus number'),
                        'capacity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Bus capacity'),
                        'amenities': openapi.Schema(type=openapi.TYPE_STRING, description='Bus amenities'),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Creation timestamp'),
                        'images': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING, description='URL of the bus image')
                        ),
                        'routes': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the route'),
                                    'origin': openapi.Schema(type=openapi.TYPE_STRING, description='Route origin'),
                                    'destination': openapi.Schema(type=openapi.TYPE_STRING, description='Route destination'),
                                    'distance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Distance of the route'),
                                }
                            )
                        ),
                        'schedules': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the schedule'),
                                    'bus': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bus'),
                                    'route': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the route'),
                                    'departure_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Departure time'),
                                    'arrival_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Arrival time'),
                                    'price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Price of the schedule'),
                                    'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Currency of the price'),
                                }
                            )
                        ),
                    }
                )
            )
        ),
        500: 'Internal Server Error'
    },
    operation_description="Retrieve a list of all buses with their images, routes, and schedules."
)
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
 
    
@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'bus': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bus'),
                            'operator': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the operator'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the bus'),
                            'bus_number': openapi.Schema(type=openapi.TYPE_STRING, description='Bus number'),
                            'capacity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Bus capacity'),
                            'amenities': openapi.Schema(type=openapi.TYPE_STRING, description='Bus amenities'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Creation timestamp'),
                        }
                    ),
                    'images': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING, description='URL of the bus image')
                    ),
                    'route': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the route'),
                            'origin': openapi.Schema(type=openapi.TYPE_STRING, description='Route origin'),
                            'destination': openapi.Schema(type=openapi.TYPE_STRING, description='Route destination'),
                            'distance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Distance of the route'),
                        }
                    ),
                    'schedule': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the schedule'),
                                'bus': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bus'),
                                'route': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the route'),
                                'departure_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Departure time'),
                                'arrival_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Arrival time'),
                                'price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Price of the schedule'),
                                'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Currency of the price'),
                            }
                        )
                    )
                }
            )
        ),
        404: openapi.Response('Bus not found'),
        500: openapi.Response('Internal Server Error'),
    },
    operation_description="Retrieve detailed information about a specific bus, including images, route, and schedule."
)
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
 
    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Amount to be collected'),
            'number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number or identifier for the payer')
        },
        required=['amount', 'number']
    ),
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the collection initiation'),
                            'transaction_id': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction ID from Campay'),
                            'amount': openapi.Schema(type=openapi.TYPE_STRING, description='Amount collected'),
                            'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Currency of the amount'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the transaction'),
                            'external_reference': openapi.Schema(type=openapi.TYPE_STRING, description='External reference for the transaction'),
                            # Add other fields from `collect` response if necessary
                        }
                    )
                }
            )
        ),
        400: openapi.Response('Bad Request'),
        500: openapi.Response('Internal Server Error'),
    },
    operation_description="Initiate a payment collection with Campay. Provide the amount and payer's phone number."
)
@api_view(['POST'])
def pay(request):
    data = request.data
    amount = data.get('amount')
    number = data.get('number')
    
    try:
        collect = campay.initCollect({
            "amount": str(amount),
            "currency": "XAF",
            "from": str(number),
            "description": "some description",
            "external_reference": "",
        })
        response = {
            'data': collect
        }
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'bus': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bus')
                },
                required=['id']
            ),
            'seats_booked': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of seats booked'),
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number of the user')
        },
        required=['bus', 'seats_booked', 'phone_number']
    ),
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the request'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message with details'),
                    'payment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the payment')
                }
            )
        ),
        400: openapi.Response(
            'Bad Request',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Error status'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        ),
        404: openapi.Response(
            'Not Found',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Error status'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Error status'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        )
    },
    operation_description="Create a booking and initiate payment process. Requires bus ID, number of seats, and phone number."
)
@api_view(['POST'])
def book(request):
    user = request.user
    data = request.data
    
    try:
        bus_id = data['bus']['id']
        schedule = Schedule.objects.get(bus=bus_id)
    except Schedule.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Schedule does not exist for the given bus.'
        }, status=status.HTTP_404_NOT_FOUND)
    except KeyError:
        return Response({
            'status': 'error',
            'message': 'Bus ID is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        seats_booked = data['seats_booked']
        phone_number = data['phone_number']
    except KeyError as e:
        return Response({
            'status': 'error',
            'message': f'Missing field: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                schedule=schedule,
                seats_booked=seats_booked,
                total_price=schedule.price * seats_booked,
                status='PENDING',
            )

            payment = Payment.objects.create(
                user=user,
                booking=booking,
                amount=booking.total_price,
                currency='XAF',
            )
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error creating booking or payment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        initiate_payment_task.delay(payment.id, booking.id, booking.total_price, booking.schedule.currency, phone_number)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error initiating payment task: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'status': 'success',
        'message': 'Payment process has been initiated.',
        'payment_id': payment.id
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the request'),
                    'balance': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current balance of the operator')
                }
            )
        ),
        404: openapi.Response(
            'Not Found',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Error status'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        )
    },
    operation_description="Retrieve the current balance of the logged-in operator, including bookings and withdrawals."
)
@api_view(['GET'])
def operator_balance(request):
    user = request.user
    try:
        operator = BusOperator.objects.get(user=user)
    except BusOperator.DoesNotExist:
        return Response({"error": "Operator not found."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        with transaction.atomic():
            operator_buses = Bus.objects.filter(operator=operator)
            operator_schedules = Schedule.objects.filter(bus__in=operator_buses)
            operator_bookings = Booking.objects.filter(schedule__in=operator_schedules)
            balance = operator_bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0
            withdrawals = Withdrawals.objects.filter(operator=operator)
            withdrawal_sum = withdrawals.aggregate(Sum('amount'))['amount__sum'] or 0
            balance = int(balance) - int(withdrawal_sum) 

        return Response({
            'status': 'success',
            'balance': balance
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error getting balance: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
        
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['amount', 'phone_number'],
        properties={
            'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='Amount to withdraw'),
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number for disbursement')
        }
    ),
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the request'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                }
            )
        ),
        404: openapi.Response(
            'Not Found',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Error status'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        )
    },
    operation_description="Initiate a withdrawal process for the logged-in operator. This triggers a disbursement task."
)
@api_view(['POST'])
def withdraw(request):
    user = request.user
    data = request.data
    amount = data.get('amount')
    phone_number = data.get('phone_number')
    
    try:
        operator = BusOperator.objects.get(user=user)
        operator_id = operator.id
    except BusOperator.DoesNotExist:
        return Response({"error": "Operator not found."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        disburse.delay(amount, phone_number, operator_id)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error initiating disburse task: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    return Response({
        'status': 'success',
        'message': 'Withdrawal process has been initiated.',
    }, status=status.HTTP_200_OK)
    
  
@api_view(['GET'])  
def operator_details(request):
    user = request.user
    data = request.data
    operator_id = data.get('id')
    
    try:
        operator = BusOperator.objects.get(id=operator_id)
        operator_images = BusOperatorImage.objects.filter(operator=operator)
        
        operator_data = {
            'operator': BusOperatorSerializer(operator).data,
            'images': BusOperatorImageSerializer(operator_images, many=True).data,
        }
        
        return Response(operator_data, status=status.HTTP_200_OK)
    
    except BusOperator.DoesNotExist:
        return Response({"error": "Operator not found."}, status=status.HTTP_404_NOT_FOUND)
        
