from celery import shared_task
from campay.sdk import Client as CamPayClient
from django.conf import settings
from .models import Payment, Withdrawals
from django.utils import timezone
from dotenv import load_dotenv
from notifications.tasks import *
import time
import os

load_dotenv()

@shared_task
def initiate_payment_task(payment_id, booking_id, amount, currency, phone_number):
    # Load CamPay client
    try:
        campay = CamPayClient({
            "app_username": os.getenv('CAMPAY_USERNAME'),
            "app_password": os.getenv('CAMPAY_PASSWORD'),
            "environment": "DEV"
        })
        print("CamPay client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize CamPay client: {e}")
        return

    # Retrieve payment record
    try:
        payment = Payment.objects.get(id=payment_id)
        print(f"Payment record found: {payment}")
    except Payment.DoesNotExist:
        print(f"Payment with ID {payment_id} does not exist.")
        return
    except Exception as e:
        print(f"Error retrieving payment record: {e}")
        return

    # Attempt to initiate payment
    try:
        print(f"Initiating payment collection for amount: {amount}, phone_number: {phone_number}")
        response = campay.initCollect({
            "amount": str(amount),
            "currency": "XAF",
            "from": str(phone_number),
            "description": f"Payment for Booking {booking_id}",
            "external_reference": str(booking_id),
        })
        payment.payment_reference = response.get('reference')
        payment.status = response.get('status', 'PENDING')
        payment.save()

        print(f"Payment initiated. Reference: {payment.payment_reference}, Status: {payment.status}")
    except Exception as e:
        print(f"Error during payment initiation: {e}")
        payment.status = 'FAILED'
        payment.description = f'Payment initiation failed: {str(e)}'
        payment.save()
        return

    # Check payment status periodically
    if payment.status == 'PENDING':
        try:
            max_checks = 10
            check_interval = 10
            print("Checking payment status...")

            for attempt in range(max_checks):
                status_response = campay.get_transaction_status({
                    "reference": payment.payment_reference,
                })
                payment_status = status_response.get('status')
                print(f"Check {attempt + 1}/{max_checks}: Payment status is {payment_status}")

                if payment_status != 'PENDING':
                    payment.status = payment_status
                    payment.save()
                    print(f"Final payment status: {payment.status}")
                                    
                    if payment_status == 'SUCCESSFUL':
                        booking_notification.delay(booking_id, payment.booking.user.id)
                        
                    break

                time.sleep(check_interval)
        except Exception as e:
            print(f"Error checking payment status: {e}")
            payment.status = 'FAILED'
            payment.description = f'Error checking payment status: {str(e)}'
            payment.save()

    # Fallback to payment link creation if initial attempt fails
    if payment.status == 'FAILED':
        try:
            print("Attempting to create payment link as fallback...")
            link_response = campay.get_payment_link({
                "amount": str(amount),
                "currency": currency,
                "description": f"Payment for Booking {booking_id}",
                "external_reference": str(booking_id),
                "from": phone_number,
                "first_name": payment.user.first_name,
                "last_name": payment.user.last_name,
                "email": payment.user.email or '',
                "redirect_url": "https://mysite.com/success/",
                "failure_redirect_url": "https://mysite.com/failure/",
                "payment_options": "MOMO",
            })
            payment.payment_link = link_response.get('link')
            payment.status = 'PENDING'
            payment.save()

            print(f"Payment link created: {payment.payment_link}")

            for attempt in range(max_checks):
                status_response = campay.get_transaction_status({
                    "reference": payment.payment_reference,
                })
                payment_status = status_response.get('status')
                print(f"Check {attempt + 1}/{max_checks}: Payment status is {payment_status}")

                if payment_status != 'PENDING':
                    payment.status = payment_status
                    payment.save()
                    print(f"Final payment status: {payment.status}")
                    break

                time.sleep(check_interval)
        except Exception as fallback_e:
            print(f"Fallback failed: {fallback_e}")
            payment.status = 'FAILED'
            payment.description = f'InitCollect failed: {str(e)}, Payment link failed: {str(fallback_e)}'
            payment.save()
 
@shared_task           
def disburse(amount, phone_number, operator_id, reference=None):
    operator = BusOperator.objects.get(id=operator_id)
    try:
        response = campay.disburse({
            "amount": str(amount),
            "to": str(phone_number),
            "currency": "XAF",
            "description": "withdrawal",
            "external_reference": ""
        })
        if response.get('status') == "SUCCESSFUL":
            withdrawal = Withdrawals.objects.create(
                operator=operator,
                amount=amount,
                receiver=phone_number,
                description="withdrawal",
                reference=None
            )
            withdrawal.save()
            print(f"{amount} successful sent out")
    except Exception as e:
        return f"error: {e}"
