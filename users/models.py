from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# Custom user manager
class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone number must be provided')
        
        if not phone_number.startswith('+237'):
            phone_number = '+237' + phone_number
        
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, password, **extra_fields)

# Custom user model
class User(AbstractBaseUser, PermissionsMixin):
    CUSTOMER = 'CUSTOMER'
    OPERATOR = 'OPERATOR'
    ADMIN = 'ADMIN'
    
    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (OPERATOR, 'Operator'),
        (ADMIN, 'Admin'),
    ]
    phone_number = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=CUSTOMER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 
    created_at = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"
    
class BusOperator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, blank=False, null=False)
    description = models.TextField(max_length=5000, blank=True)
    contact = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.contact})"
    
class BusOperatorImage(models.Model):
    operator = models.ForeignKey(BusOperator, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='operator_images/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.image} belongs to {self.operator}"
    