# store/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'created_at']
    list_filter = ['category_type', 'created_at']
    search_fields = ['name']

class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1
    fields = ['package_type', 'weight', 'price', 'stock_quantity']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'base_price', 'points', 'is_active', 'image_preview']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['base_price', 'points', 'is_active']
    inlines = [ProductOptionInline]
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;">', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"

@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ['product', 'package_type', 'weight', 'price', 'stock_quantity']
    list_filter = ['package_type', 'product__category']
    search_fields = ['product__name']
    list_editable = ['price', 'stock_quantity']

class ProductPromotionInline(admin.TabularInline):
    model = ProductPromotion
    extra = 1

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_rate', 'start_date', 'end_date', 'is_active', 'tag_text']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name']
    list_editable = ['discount_rate', 'is_active', 'tag_text']
    inlines = [ProductPromotionInline]
    
    fieldsets = (
        ('Promotion Details', {
            'fields': ('name', 'discount_rate', 'tag_text')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
    )

@admin.register(ProductPromotion)
class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = ['product', 'promotion', 'promotional_price', 'promotion_active']
    list_filter = ['promotion__is_active', 'promotion__start_date']
    search_fields = ['product__name', 'promotion__name']
    
    def promotion_active(self, obj):
        return obj.promotion.is_active
    promotion_active.boolean = True
    promotion_active.short_description = "Active"

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'order', 'is_active', 'link']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    ordering = ['order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;">', obj.image.url)
        return "No Image"
    image_preview.short_description = "Preview"

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['get_total_price']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at', 'item_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_amount', 'status', 'points_used', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    readonly_fields = ['order_number', 'created_at', 'qr_code_preview']
    list_editable = ['status']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'created_at')
        }),
        ('Payment Details', {
            'fields': ('total_amount', 'points_used', 'points_discount')
        }),
        ('QR Code', {
            'fields': ('qr_code_preview',)
        }),
    )
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="200">', obj.qr_code.url)
        return "No QR Code"
    qr_code_preview.short_description = "QR Code"

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'bank_name', 'points_to_currency_rate', 'referral_points']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name',)
        }),
        ('Banking Details', {
            'fields': ('bank_name', 'bank_account_name', 'bank_account_number')
        }),
        ('Points System', {
            'fields': ('points_to_currency_rate', 'referral_points'),
            'description': 'Configure how points work in your system'
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one SiteSettings instance
        return not SiteSettings.objects.exists()
