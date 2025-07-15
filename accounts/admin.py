# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, PointsHistory

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ['member_number', 'referral_code', 'created_at']

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_member_number', 'get_points', 'is_staff')
    list_filter = UserAdmin.list_filter + ('userprofile__created_at',)
    
    def get_member_number(self, obj):
        return obj.userprofile.member_number
    get_member_number.short_description = 'Member #'
    
    def get_points(self, obj):
        return obj.userprofile.points
    get_points.short_description = 'Points'

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'member_number', 'points', 'phone_number', 'referred_by', 'created_at']
    list_filter = ['created_at', 'referred_by']
    search_fields = ['user__username', 'user__email', 'member_number', 'phone_number']
    readonly_fields = ['member_number', 'referral_code', 'created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'member_number', 'referral_code', 'created_at')
        }),
        ('Contact Details', {
            'fields': ('phone_number', 'address')
        }),
        ('Points & Referrals', {
            'fields': ('points', 'referred_by')
        }),
    )

@admin.register(PointsHistory)
class PointsHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'points', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        # Prevent manual addition of points history
        return False

# Custom admin site configuration
admin.site.site_header = "Fresh Market Admin"
admin.site.site_title = "Fresh Market"
admin.site.index_title = "Welcome to Fresh Market Administration"

# Add custom admin dashboard views
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard with statistics"""
    
    # Get date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic statistics
    total_products = Product.objects.filter(is_active=True).count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Revenue statistics
    total_revenue = Order.objects.exclude(status='cancelled').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    weekly_revenue = Order.objects.filter(
        created_at__gte=week_ago,
        status__in=['processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        created_at__gte=month_ago,
        status__in=['processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Product statistics
    low_stock_products = ProductOption.objects.filter(stock_quantity__lt=10)
    
    # Popular products (based on order frequency)
    popular_products = Product.objects.annotate(
        order_count=Count('options__orderitem')
    ).order_by('-order_count')[:5]
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    context = {
        'total_products': total_products,
        'total_users': total_users,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'low_stock_products': low_stock_products,
        'popular_products': popular_products,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'admin/dashboard.html', context)

# Add custom URLs to admin
from django.contrib import admin
from django.urls import path

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', admin_dashboard, name='admin_dashboard'),
        ]
        return custom_urls + urls

# Replace default admin site
admin.site.__class__ = CustomAdminSite
