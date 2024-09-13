from django.core.mail import send_mail

def send_otp_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}'
    email_from = None
    recipient_list = [email]
    
    send_mail(subject, message, email_from, recipient_list)
