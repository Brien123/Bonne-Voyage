from django.shortcuts import render
from users.models import *
from buses.models import *
from notifications.models import *
from django.db.models import Count
# Create your views here.

def dashboard_view(request):
    booking_status_labels = list(Booking.objects.values_list('status', flat=True).distinct())
    booking_status_counts = [Booking.objects.filter(status=status).count() for status in booking_status_labels]

    route_labels = [f"{r.origin} to {r.destination}" for r in Route.objects.all()]
    route_counts = [Booking.objects.filter(schedule__route=r).count() for r in Route.objects.all()]
    
    context = {
        'user_count': User.objects.count(),
        'bus_count': Bus.objects.count(),
        'bookings_count': Booking.objects.count(),
        'booking_status_labels': booking_status_labels,
        'booking_status_counts': booking_status_counts,
        'route_labels': route_labels,
        'route_counts': route_counts,
    }
    return render(request, 'dashboard/dashboard.html', context)


def index(request):
    return render(request, 'dashboard/dashboard.html') 
