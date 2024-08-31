from django.db import models
from django.utils import timezone
from users.models import BusOperator, User

# Create your models here.
class Bus(models.Model):
    operator = models.ForeignKey(BusOperator, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    bus_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    amenities = models.TextField(blank=True, null=True)
    # image = models.ImageField(upload_to='bus_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.bus_number} {self.operator.name}"
    
class Route(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, default=3)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=6, decimal_places=2, help_text='Distance in kilometers')
        
    def __str__(self):
        return f"{self.origin} to {self.destination} ({self.distance} km)"
    
class BusImage(models.Model):
    bus = models.ForeignKey(Bus, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='bus_images/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Image for {self.bus.bus_number} ({self.bus.operator.name})"
    
class Schedule(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(default='XAF', max_length=3)
    
    def __str__(self):
        return f"{self.bus.bus_number} owned by {self.bus.operator.name} goes from {self.route.origin} to {self.route.destination} for {self.price} {self.currency}"
    
    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError('Arrival time must be after the departure time.')

    class Meta:
        unique_together = ('bus', 'route', 'departure_time')
        
class Booking(models.Model):
    choices = [
        ('CONFIRMED', 'confirmed'),
        ('CANCELLED', 'cancelled'),
        ('PENDING', 'pending'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Bookings')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='Bookings')
    seats_booked = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=choices)
    
    def __str__(self):
        return f"Booking {self.id} by {self.user.first_name} for {self.schedule.route}"
    
    def clean(self):
        booked_seats = Booking.objects.filter(
            schedule=self.schedule,
            status='CONFIRMED' 
        ).aggregate(total=models.Sum('seats_booked'))['total'] or 0
        
        available_seats = self.schedule.bus.capacity - booked_seats
        
        if self.seats_booked > available_seats:
            raise ValidationError(f'Cannot book {self.seats_booked} seats. Only {available_seats} seats are available.')

    def save(self, *args, **kwargs):
        self.total_price = self.seats_booked * self.schedule.price
        super().save(*args, **kwargs)
    
class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    last_checked = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Payment {self.id} - {self.status}'   
    
class Withdrawals(models.Model):
    operator = models.ForeignKey(BusOperator, on_delete=models.CASCADE)
    amount = models.CharField(max_length=10)
    receiver = models.CharField(max_length=10)
    description = models.CharField(max_length=2560)
    reference = models.CharField(max_length=10)
