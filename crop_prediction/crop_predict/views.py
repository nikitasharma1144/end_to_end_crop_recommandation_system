from pathlib import Path
import pickle
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .loader import predict_one
from .models import Prediction
from .models import UserProfile
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_date
from django.contrib.auth import logout


# load prediction model from the workspace, if available
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / 'end_to_end_crop_recommandation_system' / 'random_forest_model.pkl'
model = None
if MODEL_PATH.exists():
    try:
        with open(MODEL_PATH, 'rb') as model_file:
            model = pickle.load(model_file)
    except Exception:
        model = None

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not username or not email or not password:
            messages.error(request, 'Username, email, and password are required.')
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose another.')
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        auth_login(request, user)
        messages.success(request, 'Account created successfully. You are now logged in.')
        return redirect('home')

    return render(request, 'signup.html')

def result(request):
    return render(request, 'result.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'login.html')

        user_obj = User.objects.filter(email=email).first()
        if user_obj is None:
            messages.error(request, 'No account found for that email.')
            return render(request, 'login.html')

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('home')

        messages.error(request, 'Invalid credentials. Please check your email and password.')
    return render(request, 'login.html')


def change_password_view(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Run your validations sequentially
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect")
            return render(request, 'change_password.html')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match")
            return render(request, 'change_password.html')

        # Save updates safely
        request.user.set_password(new_password)
        request.user.save()
        
        messages.success(request, "Password updated successfully!")
        return redirect('home')

    return render(request, 'change_password.html')

def logout_view(request):
    auth_logout(request)
    return redirect('home')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def index(request):
    return render(request, 'index.html')

@login_required(login_url='login')
def predict(request):
    context = {}
    
    if request.method == "POST":
        # Capture raw telemetry inputs from the front-end form
        feature_dict = {
            'N': request.POST.get('nitrogen'),
            'P': request.POST.get('phosphorus'),
            'K': request.POST.get('potassium'),
            'temperature': request.POST.get('temperature'),
            'humidity': request.POST.get('humidity'),
            'ph': request.POST.get('ph'),
            'rainfall': request.POST.get('rainfall'),
        }
        
        try:
            # Send values over to loader processing layer
            crop_result = predict_one(feature_dict)
            
            # Store inputs and final result inside context dict to show the user
            context['result'] = crop_result
            context['inputs'] = feature_dict

            # Save prediction history for logged-in users
            Prediction.objects.create(
                user=request.user,
                result=str(crop_result),
                nitrogen=float(feature_dict['N'] or 0),
                phosphorus=float(feature_dict['P'] or 0),
                potassium=float(feature_dict['K'] or 0),
                temperature=float(feature_dict['temperature'] or 0),
                humidity=float(feature_dict['humidity'] or 0),
                ph=float(feature_dict['ph'] or 0),
                rainfall=float(feature_dict['rainfall'] or 0),
            )
            
        except Exception as e:
            context['error'] = f"Prediction failed: {str(e)}"
            
    return render(request, 'index.html', context)


@login_required(login_url='login')
def user_history_view(request):
    predictions = Prediction.objects.filter(user=request.user)
    return render(request, 'history.html', locals())


@login_required(login_url='login')
def user_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id, user=request.user)
    prediction.delete()
    messages.success(request, "Entry removed from history")
    return redirect('user_history')


@login_required(login_url='login')
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    full_name = request.user.get_full_name()

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')

        if name:
            parts = name.strip().split(' ', 1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts) > 1 else ""

        profile.phone = phone
        request.user.save()
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        full_name = request.user.get_full_name()

    return render(request, 'profile.html', {
        'profile': profile,
        'full_name': full_name,
    })



 # Make sure your Prediction model is imported!

# Helper function to check if the user is a logged-in Admin/Staff
def is_admin_staff(user):
    return user.is_authenticated and user.is_staff

# 1. Admin Login View
def admin_login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '')

        # Allow admin login by exact username or email address
        user_obj = User.objects.filter(username__iexact=identifier).first()
        if user_obj is None:
            user_obj = User.objects.filter(email__iexact=identifier).first()

        if user_obj is None:
            messages.error(request, "Invalid admin username or email.")
            return redirect('admin_login')

        user = authenticate(request, username=user_obj.username, password=password_input)

        if user is not None and user.is_staff:
            auth_login(request, user)
            messages.success(request, "Logged in successfully to Admin Panel!")
            return redirect('admin_dashboard')

        messages.error(request, "Invalid login credentials or not authorized for admin access.")
        return redirect('admin_login')

    return render(request, 'admin_login.html')

def is_staff(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_staff, login_url='admin_login')
def admin_dashboard_view(request):
    # Core statistics counter 
    total_users = User.objects.filter(is_staff=False).count()
    total_predictions = Prediction.objects.count()
    
    # --- Logic 1: Fetch and group Top 10 Recommended Crops for Bar Chart ---
    # Group entries by predicted crop labels, annotate them with unique count aggregates 'c', and order largest to smallest
    crop_qs = Prediction.objects.values('result').annotate(c=Count('id')).order_by('-c')[:10]
    
    crop_labels = [item['result'].title() for item in crop_qs]
    crop_counts = [item['c'] for item in crop_qs]
    
    # --- Logic 2: Fetch Last 7 Days Prediction Entries for Line Chart ---
    today = timezone.localdate()
    day_labels = []
    day_counts = []
    
    # Loop backwards across the last 7 calendar days
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        
        # Human-friendly string formatting (e.g., "08 Jun")
        formatted_day = target_date.strftime('%d %b')
        day_labels.append(formatted_day)
        
        # Filter total count entries targeting the exact day match
        predictions_on_day = Prediction.objects.filter(created_at__date=target_date).count()
        day_counts.append(predictions_on_day)
        
    # Packaging Python Lists into secure JSON format strings for JavaScript consumption
    context = {
        'total_users': total_users,
        'total_predictions': total_predictions,
        'crop_labels_json': json.dumps(crop_labels),
        'crop_counts_json': json.dumps(crop_counts),
        'day_labels_json': json.dumps(day_labels),
        'day_counts_json': json.dumps(day_counts),
    }
    
    return render(request, 'admin_dashboard.html', context)



# Access-control validation checking helper function
def is_staff(user):
    return user.is_authenticated and user.is_staff

# 1. View function to list all registered system end-users
@user_passes_test(is_staff, login_url='admin_login')
def admin_users_view(request):
    # Fetch all users who are not administrative staff members
    users = User.objects.filter(is_staff=False)
    
    # Passing data explicitly using a dictionary template context
    return render(request, 'admin_view_users.html', {'users': users})

# 2. View function to securely delete a user by primary key (ID)
@user_passes_test(is_staff, login_url='admin_login')
def admin_user_delete(request, id):
    # Fetch the user matching the given ID or throw a 404 error if not found
    user_to_delete = get_object_or_404(User, id=id)
    
    # Deleting the user automatically cascade-deletes their related profile info
    user_to_delete.delete()
    
    messages.success(request, "User deleted successfully")
    return redirect('admin_users_view')


def is_staff(user):
    return user.is_authenticated and user.is_staff

# 1. Main View Dashboard with Filtering Capabilities
@user_passes_test(is_staff, login_url='admin_login')
def admin_view_predictions(request):
    # Retrieve base query optimization minimizing SQL hitting cycles
    qs = Prediction.objects.select_related('user').all()
    
    # Extract query filter values from the GET Request 
    crop_filter = request.GET.get('crop')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    # Categorical Filtering implementation
    if crop_filter and crop_filter != 'all':
        qs = qs.filter(predicted_label__iexact=crop_filter)
        
    # Date Filtering using parse_date utility to translate strings to date objects
    d_start = parse_date(start_date) if start_date else None
    d_end = parse_date(end_date) if end_date else None
    
    if d_start:
        qs = qs.filter(created_at__date__gte=d_start)
    if d_end:
        qs = qs.filter(created_at__date__lte=d_end)
        
    # Extract clean, distinct alphabetical choices to populate the dropdown menu
    crops_list = Prediction.objects.order_by('predicted_label').values_list('predicted_label', flat=True).distinct()
    
    context = {
        'predictions': qs,
        'crops': crops_list,
        'current_crop': crop_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_view_predictions.html', context)

# 2. Deletion processing endpoint logic
@user_passes_test(is_staff, login_url='admin_login')
def admin_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id)
    prediction.delete()
    messages.success(request, "Prediction entry deleted successfully.")
    return redirect('admin_view_predictions')

# 3. Clean targeted session separation logic for admin
def admin_logout(request):
    logout(request)
    return redirect('admin_login')    
