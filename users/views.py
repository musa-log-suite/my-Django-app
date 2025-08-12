# 🔐 Django Auth & Core
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.messages import get_messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone

# 👤 User Model
User = get_user_model()

# 🧾 Forms
from users.forms import UserRegisterForm, PasswordResetRequestForm

# 🔐 OTP Services
from users.services.otp_services import generate_otp_for_user, verify_otp

# ⚙️ Django REST Framework
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

# 📄 Swagger Documentation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# 🧬 Serializers
from .serializers import (
    UserRegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

# 📡 Example API View
class MyView(APIView):
    @swagger_auto_schema(operation_description="Get example response")
    def get(self, request):
        return Response({"message": "Hello, world!"}) 
                                
# Template-Based Views
# ─────────────────────────────────────────────────────────────

# ✅ Home Page View
def home_view(request):
    return render(request, "users/home.html")


# ✅ Custom Login View
class CustomLoginView(LoginView):
    template_name = "users/login.html"
    success_url = reverse_lazy("users:user-profile")

    def get_success_url(self):
        return self.success_url


# ✅ Enhanced Registration View with OTP, Validation, and Auto-login
def register_view(request):
    form = UserRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)

        # Optional: Validate phone/email here
        if not user.email and not user.phone_number:
            messages.error(request, "Please provide a valid email or phone number.")
            return render(request, "users/register.html", {"form": form})

        user.save()

        try:
            generate_otp_for_user(user, purpose="signup")
            login(request, user)  # Auto-login after registration
            messages.success(request, "Registration successful. OTP has been sent.")
        except RuntimeError:
            messages.warning(request, "User created, but OTP could not be sent.")
        return redirect("users:user-profile")

    return render(request, "users/register.html", {"form": form})


# ✅ Password Reset Request View
def request_password_reset(request):
    form = PasswordResetRequestForm(request.POST or None)

    # ✅ Clear any lingering messages
    list(get_messages(request))

    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["phone_or_email"]
        request.session["reset_identifier"] = identifier  # ✅ Updated key

        # ✅ Find user by phone or email
        try:
            user = User.objects.get(Q(email=identifier) | Q(phone_number=identifier))
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return render(request, "users/request_password_otp.html", {"form": form})

        # ✅ Generate OTP
        try:
            otp_obj = generate_otp_for_user(user, purpose="password_reset")
            request.session["otp_created_at"] = otp_obj.created_at.isoformat()

            messages.success(request, "OTP has been sent to your phone or email.")
            messages.info(request, f"Test OTP: {otp_obj.code}")  # For dev only

            return redirect("users:template-recover-password")
        except RuntimeError as e:
            print(f"❌ OTP dispatch failed: {e}")
            messages.error(request, str(e))
            return render(request, "users/request_password_otp.html", {"form": form})

    return render(request, "users/request_password_otp.html", {"form": form})


# ✅ Password Recovery View
def recover_password(request):
    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        identifier = request.session.get("reset_email")  # could be email or phone

        # ✅ Check session
        if not identifier:
            messages.error(request, "Session expired. Please start again.")
            return redirect("users:template-request-password-otp")

        # ✅ Validate password match
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "recover_password.html")

        # ✅ Validate password length
        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, "recover_password.html")

        # ✅ Find user by email or phone
        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(phone_number=identifier).first()
        )
        if not user:
            messages.error(request, "User not found.")
            return redirect("users:template-request-password-otp")

        # ✅ Verify OTP
        success, message = verify_otp(user, otp, purpose="password_reset")
        if success:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successful.")
            return redirect("users:template-login")
        else:
            messages.error(request, message)

    return render(request, "recover_password.html")
    
 
def resend_password_otp(request):
    identifier = request.session.get("reset_identifier")  # or "reset_email" if you're still using that

    if not identifier:
        messages.error(request, "Session expired. Please start again.")
        return redirect("users:template-request-password-otp")

    user = (
        User.objects.filter(email=identifier).first()
        or User.objects.filter(phone_number=identifier).first()
    )

    if not user:
        messages.error(request, "User not found.")
        return redirect("users:template-request-password-otp")

    try:
        send_otp(identifier, purpose="password_reset")
        messages.success(request, "A new OTP has been sent to your phone or email.")
    except RuntimeError as e:
        messages.error(request, f"Failed to resend OTP: {str(e)}")

    return redirect("users:template-recover-password")       
        
# ─────────────────────────────────────────────────────────────
# API Views
# ─────────────────────────────────────────────────────────────

@swagger_auto_schema(
    method="post",
    operation_summary="Register a New User",
    operation_description="Creates a new user account and sends an OTP for phone verification.",
    request_body=UserRegisterSerializer,
    responses={
        201: openapi.Response(description="Registration successful. OTP sent."),
        400: openapi.Response(description="Validation error"),
        500: openapi.Response(description="Failed to send OTP")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def register_user(request):
    serializer = UserRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    try:
        generate_otp_for_user(user, purpose="signup")
    except RuntimeError:
        return Response(
            {"error": "Could not send OTP. Try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {"message": "Registration successful. OTP sent."},
        status=status.HTTP_201_CREATED
    )


@swagger_auto_schema(
    method="post",
    operation_summary="Resend OTP",
    operation_description="Resends an OTP to the user's phone or email.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["identifier", "purpose"],
        properties={
            "identifier": openapi.Schema(type=openapi.TYPE_STRING),
            "purpose": openapi.Schema(type=openapi.TYPE_STRING, enum=["signup", "login", "password_reset"])
        }
    ),
    responses={
        200: openapi.Response(description="OTP resent successfully."),
        400: openapi.Response(description="Invalid input."),
        500: openapi.Response(description="Failed to resend OTP.")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def resend_otp(request):
    identifier = request.data.get("identifier")
    purpose = request.data.get("purpose", "signup")

    user = (
        User.objects.filter(phone_number=identifier).first() or
        User.objects.filter(email=identifier).first()
    )
    if not user:
        return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        generate_otp_for_user(user, purpose=purpose)
        return Response({"message": "OTP resent successfully."}, status=status.HTTP_200_OK)
    except RuntimeError:
        return Response({"error": "Failed to resend OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="post",
    operation_summary="Request Password Reset OTP",
    operation_description="Sends an OTP to the user's phone or email for password recovery.",
    request_body=PasswordResetRequestSerializer,
    responses={
        200: openapi.Response(description="OTP sent successfully."),
        400: openapi.Response(description="Invalid input."),
        500: openapi.Response(description="Failed to send OTP.")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def request_password_reset_api(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = serializer.validated_data["identifier"]

    # ✅ Find user by phone or email
    user = (
        User.objects.filter(phone_number=identifier).first()
        or User.objects.filter(email=identifier).first()
    )

    if not user:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # ✅ Generate OTP
    try:
        generate_otp_for_user(user, purpose="password_reset")
        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)
    except RuntimeError:
        return Response({"detail": "Failed to send OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method="post",
    operation_summary="Recover Password",
    operation_description="Verifies OTP and resets the user's password.",
    request_body=PasswordResetConfirmSerializer,
    responses={
        200: openapi.Response(description="Password reset successful."),
        400: openapi.Response(description="Invalid OTP or user."),
        500: openapi.Response(description="Server error.")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def recover_password_api(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = serializer.validated_data["identifier"]
    otp = serializer.validated_data["otp"]
    new_password = serializer.validated_data["new_password"]

    # ✅ Find user by phone or email
    user = (
        User.objects.filter(phone_number=identifier).first()
        or User.objects.filter(email=identifier).first()
    )

    if not user:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # ✅ Verify OTP
    success, message = verify_otp(user, otp, purpose="password_reset")
    if not success:
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Update password
    user.set_password(new_password)
    user.save()

    return Response({"detail": "Password reset successful."}, status=status.HTTP_200_OK)
    
@swagger_auto_schema(
    method="post",
    operation_summary="Verify Phone with OTP",
    operation_description="Verifies the user's phone number using an OTP.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["phone_number", "otp"],
        properties={
            "phone_number": openapi.Schema(type=openapi.TYPE_STRING),
            "otp": openapi.Schema(type=openapi.TYPE_STRING, maxLength=6)
        }
    ),
    responses={
        200: openapi.Response(description="Phone verified successfully."),
        400: openapi.Response(description="Invalid OTP or phone number."),
        500: openapi.Response(description="Server error.")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def verify_phone(request):
    phone = request.data.get("phone_number")
    otp = request.data.get("otp")

    user = User.objects.filter(phone_number=phone).first()
    if not user:
        return Response()

@swagger_auto_schema(
    method="get",
    operation_summary="Get Authenticated User Profile",
    operation_description="Returns the profile details of the currently logged-in user.",
    responses={
        200: openapi.Response(
            description="User profile retrieved successfully.",
            examples={
                "application/json": {
                    "phone_number": "+2348000000000",
                    "email": "user@example.com",
                    "full_name": "Musa Ibrahim",
                    "is_agent": False,
                    "is_phone_verified": True
                }
            }
        ),
        401: openapi.Response(description="Authentication required")
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    data = {
        "phone_number": user.phone_number,
        "email": user.email,
        "full_name": user.full_name,
        "is_agent": user.is_agent,
        "is_phone_verified": user.is_phone_verified,
    }
    return Response(data, status=status.HTTP_200_OK)                