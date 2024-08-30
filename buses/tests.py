from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Bus, Schedule, Route, Booking, Payment
from users.models import User, BusOperator
from django.utils import timezone
from users.models import User, BusOperator

class BusAPITests(APITestCase):
    
    def setUp(self):
        self.client = APIClient()
        
        self.operator_user = User.objects.create_user(
            phone_number='1234567890',
            first_name='John',
            last_name='Doe',
            password='password123',
            role='OPERATOR'
        )
        self.client.force_authenticate(user=self.operator_user)
        
        self.bus_operator = BusOperator.objects.create(
            user=self.operator_user,
            name="Test Bus Operator"
        )
        
        self.bus_data = {
            'name': 'Test Bus',
            'bus_number': '123ABC',
            'capacity': 40,
            'amenities': 'Wi-Fi, Reclining Seats',
            'operator': self.bus_operator.id,
            'origin': 'City A',
            'destination': 'City B',
            'distance': 200,
            'departure_time': timezone.now(),
            'arrival_time': timezone.now() + timezone.timedelta(hours=4),
            'price': 10000,
            'currency': 'XAF'
        }
        
    def test_create_bus(self):
        url = reverse('bus')
        response = self.client.post(url, self.bus_data, format='json')
        
        # print(response.data)  # Add this line to inspect the response data
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Bus successfully created')  # Adjusted based on actual response structure
        self.assertEqual(Bus.objects.count(), 1)

    
    def test_create_schedule(self):
        bus = Bus.objects.create(
            name='Test Bus',
            bus_number='123ABC',
            capacity=40,
            amenities='Wi-Fi, Reclining Seats',
            operator=self.bus_operator
        )
        
        route = Route.objects.create(
            bus=bus,
            origin='City A',
            destination='City B',
            distance=200
        )
        
        schedule_data = {
            'bus_id': bus.id,
            'route_id': route.id,
            'departure_time': timezone.now(),
            'arrival_time': timezone.now() + timezone.timedelta(hours=4),
            'price': 10000,
            'currency': 'XAF'
        }
        
        url = reverse('schedule')
        response = self.client.post(url, schedule_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Schedule created successfully!")
        self.assertEqual(Schedule.objects.count(), 1)
    
    def test_buses_list(self):
        # Create some buses
        Bus.objects.create(
            name='Test Bus 1',
            bus_number='123ABC',
            capacity=40,
            amenities='Wi-Fi, Reclining Seats',
            operator=self.bus_operator
        )
        Bus.objects.create(
            name='Test Bus 2',
            bus_number='456DEF',
            capacity=50,
            amenities='Air Conditioning',
            operator=self.bus_operator
        )
        
        url = reverse('buses')
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_bus_detail(self):
        # Create a bus
        bus = Bus.objects.create(
            name='Test Bus',
            bus_number='123ABC',
            capacity=40,
            amenities='Wi-Fi, Reclining Seats',
            operator=self.bus_operator
        )
        
        url = reverse('bus_detail', kwargs={'id': bus.id})
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bus']['name'], bus.name)
    
    def test_book(self):
        # Create a bus and schedule
        bus = Bus.objects.create(
            name='Test Bus',
            bus_number='123ABC',
            capacity=40,
            amenities='Wi-Fi, Reclining Seats',
            operator=self.bus_operator
        )
        
        route = Route.objects.create(
            bus=bus,
            origin='City A',
            destination='City B',
            distance=200
        )
        
        schedule = Schedule.objects.create(
            bus=bus,
            route=route,
            departure_time=timezone.now(),
            arrival_time=timezone.now() + timezone.timedelta(hours=4),
            price=2,
            currency='XAF'
        )
        
        booking_data = {
            'bus': {'id': bus.id},
            'seats_booked': 2,
            'phone_number': '237xxxxxxxx'
        }
        
        url = reverse('book')
        response = self.client.post(url, booking_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(Booking.objects.count(), 1)
    
    # def test_pay(self):
    #     payment_data = {
    #         'amount': 5000,
    #         'number': '237xxxxxxxx'
    #     }
        
    #     url = reverse('pay')
    #     response = self.client.post(url, payment_data, format='json')
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertIn('data', response.data)
