## accounts/views.py
```python
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, PointsHistory
from .forms import UserRegistrationForm
from store.models import SiteSettings

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Check for referral code
            referral_code = request.POST.get('referral_code')
            if referral_code:
                try:
                    referrer_profile = UserProfile.objects.get(referral_code=referral_code)
                    user.userprofile.referred_by = referrer_profile.user
                    
                    # Add referral points
                    settings = SiteSettings.objects.first()
                    referral_points = settings.referral_points if settings else 50
                    
                    referrer_profile.points += referral_points
                    referrer_profile.save()
                    
                    user.userprofile.points += referral_points
                    user.userprofile.save()
                    
                    # Record points history
                    PointsHistory.objects.create(
                        user=referrer_profile.user,
                        transaction_type='referral',
                        points=referral_points,
                        description=f'Referral bonus for {user.username}'
                    )
                    
                    PointsHistory.objects.create(
                        user=user,
                        transaction_type='referral',
                        points=referral_points,
                        description='Welcome bonus for joining through referral'
                    )
                    
                except UserProfile.DoesNotExist:
                    messages.warning(request, 'Invalid referral code')
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('index')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    user_profile = request.user.userprofile
    points_history = PointsHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'user_profile': user_profile,
        'points_history': points_history,
    }
    return render(request, 'accounts/profile.html', context)
