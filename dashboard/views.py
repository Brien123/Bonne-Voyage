from django.shortcuts import render
from django.db.models import Count, Avg
from django.utils import timezone
from django.db.models.functions import TruncMonth
from datetime import timedelta
from users.models import User
from buses.models import Bus, Booking, Route
from notifications.models import *
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

def dashboard_view(request):
    # Booking status distribution
    booking_status_labels = list(Booking.objects.values_list('status', flat=True).distinct())
    booking_status_counts = [Booking.objects.filter(status=status).count() for status in booking_status_labels]

    # Route popularity
    routes = Route.objects.all()
    route_labels = [f"{r.origin} to {r.destination}" for r in routes]
    route_counts = [Booking.objects.filter(schedule__route=r).count() for r in routes]

    # User growth over the last year
    one_year_ago = timezone.now() - timedelta(days=365)
    user_growth_data = User.objects.filter(created_at__gte=one_year_ago) \
        .annotate(month=TruncMonth('created_at')) \
        .values('month') \
        .annotate(count=Count('id')) \
        .order_by('month')
    user_growth_labels = [data['month'].strftime('%B %Y') for data in user_growth_data]
    user_growth_counts = [data['count'] for data in user_growth_data]

    # Booking trends over the last year
    booking_trends_data = Booking.objects.filter(booking_date__gte=one_year_ago) \
        .annotate(month=TruncMonth('booking_date')) \
        .values('month') \
        .annotate(count=Count('id')) \
        .order_by('month')
    booking_trends_labels = [data['month'].strftime('%B %Y') for data in booking_trends_data]
    booking_trends_counts = [data['count'] for data in booking_trends_data]

    # Popular destinations
    popular_destinations = Booking.objects.values('schedule__route__destination') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:5]

    # Average booking value
    average_booking_value = Booking.objects.aggregate(Avg('total_price'))['total_price__avg']
    
    # Total revenue
    # operator_buses = Bus.objects.all()
    def total_revenue():
        operator_schedules = Schedule.objects.all()
        operator_bookings = Booking.objects.filter(schedule__in=operator_schedules)
        balance = operator_bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Context for the template
    context = {
        'user_count': User.objects.count(),
        'bus_count': Bus.objects.count(),
        'bookings_count': Booking.objects.count(),
        'average_booking_value': average_booking_value,
        'booking_status_labels': booking_status_labels,
        'booking_status_counts': booking_status_counts,
        'route_labels': route_labels,
        'route_counts': route_counts,
        'user_growth_labels': user_growth_labels,
        'user_growth_counts': user_growth_counts,
        'booking_trends_labels': booking_trends_labels,
        'booking_trends_counts': booking_trends_counts,
        'popular_destinations': popular_destinations,
    }

    return render(request, 'dashboard/dashboard.html', context)

def admin_notification(request):
    message = request.POST.get('message')
    
    if not message:
        return JsonResponse({'error': 'Message content is required.'}, status=400)
    
    # Create notifications for all users
    users = User.objects.all()
    notifications = [
        Notifications(recipient=user, notification_type='SYSTEM', message=message)
        for user in users
    ]
    Notifications.objects.bulk_create(notifications)

    return JsonResponse({'success': 'Notifications sent successfully.'}, status=201)

@login_required
def notification_view(request):
    return render(request, 'dashboard/admin_notification.html')
