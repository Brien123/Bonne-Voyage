from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import BusOperator, BusOperatorImage

User = get_user_model()

class UserManagementAPITestCase(APITestCase):
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            phone_number='+237670000000',
            password='testpassword',
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            role=User.CUSTOMER
        )
        self.operator = User.objects.create_user(
            phone_number='+237680000000',
            password='operatorpassword',
            first_name='Jane',
            last_name='Smith',
            email='janesmith@example.com',
            role=User.OPERATOR
        )
        self.bus_operator = BusOperator.objects.create(
            user=self.operator,
            name='Test Operator',
            description='Description of Test Operator',
            contact='+237680000000',
            email='operator@example.com'
        )
    
    def test_register_user(self):
        url = reverse('register')
        data = {
            "phone_number": "+237690000000",
            "password": "newpassword",
            "first_name": "Alice",
            "last_name": "Wonderland",
            "email": "alice@example.com",
            "role": "CUSTOMER"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertTrue(User.objects.filter(phone_number='+237690000000').exists())

    def test_register_operator_with_images(self):
        url = reverse('register')
        data = {
            "phone_number": "+237695000000",
            "password": "operatorpassword",
            "first_name": "Operator",
            "last_name": "Example",
            "email": "operator@example.com",
            "role": "OPERATOR",
            "business_name": "Operator Inc.",
            "business_description": "Best in the business",
            "business_contact": "+237695000000",
            "business_email": "contact@operator.com"
        }
        with open('test_image.jpg', 'rb') as image:
            response = self.client.post(url, data, format='multipart', files={'images': image})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        operator = User.objects.get(phone_number='+237695000000')
        self.assertTrue(BusOperator.objects.filter(user=operator).exists())
        self.assertTrue(BusOperatorImage.objects.filter(operator__user=operator).exists())

    def test_login_user(self):
        url = reverse('login')
        data = {
            "phone_number": "+237670000000",
            "password": "testpassword"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_user(self):
        url = reverse('login')
        data = {
            "phone_number": "+237000000000",
            "password": "wrongpassword"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_logout_user(self):
        url = reverse('logout')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Successfully logged out.")

    def test_edit_operator_profile(self):
        url = reverse('edit-profile')
        self.client.force_authenticate(user=self.operator)
        data = {
            "name": "Updated Operator Name",
            "description": "Updated description",
            "contact": "+237690000000",
            "email": "updated@example.com"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Profile successfully updated.")
        bus_operator = BusOperator.objects.get(user=self.operator)
        self.assertEqual(bus_operator.name, "Updated Operator Name")
        self.assertEqual(bus_operator.description, "Updated description")

    def test_edit_operator_profile_unauthorized(self):
        url = reverse('edit-profile')
        self.client.force_authenticate(user=self.user)  # Authenticate as a customer
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "User not authorized to edit profile.")

    def test_change_password(self):
        url = reverse('change-password')
        self.client.force_authenticate(user=self.user)
        data = {
            "password": "newsecurepassword"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password("newsecurepassword"))

    def test_change_password_unauthorized(self):
        url = reverse('change-password')
        data = {
            "password": "newpassword"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
