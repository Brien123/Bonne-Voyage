from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import BusOperator

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    business_name = serializers.CharField(required=False, allow_blank=True)
    business_description = serializers.CharField(required=False, allow_blank=True)
    business_contact = serializers.CharField(required=False, allow_blank=True)
    business_email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'phone_number', 'password', 'first_name', 'last_name', 'email', 'role',
            'business_name', 'business_description', 'business_contact', 'business_email'
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            # roles = validated_data.get('role', User.CUSTOMER),
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            role=validated_data.get('role', User.CUSTOMER),
        )

        if user.role == User.OPERATOR:
            BusOperator.objects.create(
                user=user,
                name=validated_data.get('business_name', ''),
                description=validated_data.get('business_description', ''),
                contact=validated_data.get('business_contact', user.phone_number),
                email=validated_data.get('business_email', user.email),
            )

        return user

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone_number = data.get("phone_number")
        password = data.get("password")
        
        if not phone_number.startswith('+237'):
            phone_number = '+237' + phone_number

        user = User.objects.filter(phone_number=phone_number).first()
        if user and user.check_password(password):
            return user
        raise serializers.ValidationError("Invalid phone number or password.")
    
class BusOperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusOperator
        fields = ('id', 'user', 'name', 'description', 'contact', 'email', 'created_at')
        read_only_fields = ('created_at', 'user')
        
class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'password')

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])  
        instance.save()
        return instance
    
