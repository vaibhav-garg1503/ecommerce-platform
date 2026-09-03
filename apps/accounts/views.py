from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from .models import User, Address
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, 
    AddressForm, PasswordResetRequestForm, SetNewPasswordForm
)

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False # Require email verification
            user.save()
            
            # Send verification email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
            )
            
            html_message = render_to_string('accounts/emails/verify_email.html', {
                'user': user,
                'verification_link': verification_link
            })
            
            send_mail(
                subject='Verify your email address',
                message=f'Please click the following link to verify your email: {verification_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
            
            messages.success(request, "Registration successful. Please check your email to verify your account.")
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Your email has been verified successfully!')
        return redirect('accounts:profile')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('accounts:login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get('next', 'accounts:profile')
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account is disabled.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})

@login_required
def address_create_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            elif not Address.objects.filter(user=request.user).exists():
                address.is_default = True
                
            address.save()
            messages.success(request, 'Address added successfully.')
            return redirect('accounts:address_list')
    else:
        form = AddressForm()
        
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add Address'})

@login_required
def address_update_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            
            if updated_address.is_default:
                Address.objects.filter(user=request.user, is_default=True).exclude(pk=pk).update(is_default=False)
                
            updated_address.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)
        
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})

@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully.')
        return redirect('accounts:address_list')
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})

@login_required
def address_set_default_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()
        messages.success(request, 'Default address updated.')
    return redirect('accounts:address_list')

def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    reset_link = request.build_absolute_uri(
                        reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                    )
                    
                    html_message = render_to_string('accounts/emails/password_reset.html', {
                        'user': user,
                        'reset_link': reset_link
                    })
                    
                    send_mail(
                        subject='Password Reset Request',
                        message=f'Please click the following link to reset your password: {reset_link}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message
                    )
            messages.success(request, 'If an account exists with this email, we have sent instructions to reset your password.')
            return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset.html', {'form': form})

def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password'])
                user.save()
                messages.success(request, 'Password reset successfully. You can now log in.')
                return redirect('accounts:login')
        else:
            form = SetNewPasswordForm()
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('accounts:login')

@login_required
def resend_verification(request):
    user = request.user

    if user.is_email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('accounts:profile')

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    verification_link = request.build_absolute_uri(
        reverse(
            'accounts:verify_email',
            kwargs={
                'uidb64': uid,
                'token': token,
            }
        )
    )

    html_message = render_to_string(
        'accounts/emails/verify_email.html',
        {
            'user': user,
            'verification_link': verification_link,
        }
    )

    send_mail(
        subject='Verify your email address',
        message=f'Please click the following link to verify your email: {verification_link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )

    messages.success(
        request,
        'A new verification email has been sent to your email address.'
    )

    return redirect('accounts:profile')