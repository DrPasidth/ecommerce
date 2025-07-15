# Management commands for initial setup
# Create file: store/management/commands/setup_initial_data.py

import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import *
from accounts.models import *

class Command(BaseCommand):
    help = 'Set up initial data for the e-commerce site'
    
    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@freshmarket.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created'))
        
        # Create categories
        categories = [
            ('Leafy Greens', 'vegetable'),
            ('Root Vegetables', 'vegetable'),
            ('Tropical Fruits', 'fruit'),
            ('Citrus Fruits', 'fruit'),
            ('Herbs & Spices', 'other'),
        ]
        
        for name, cat_type in categories:
            Category.objects.get_or_create(
                name=name,
                defaults={'category_type': cat_type}
            )
        
        # Create site settings
        SiteSettings.objects.get_or_create(
            id=1,
            defaults={
                'company_name': 'Fresh Market',
                'bank_name': 'Bangkok Bank',
                'bank_account_name': 'Fresh Market Co., Ltd.',
                'bank_account_number': '123-456-7890',
                'points_to_currency_rate': 0.10,  # 100 points = 10 baht
                'referral_points': 50,
            }
        )
        
        # Create sample products
        vegetables_cat = Category.objects.get(name='Leafy Greens')
        fruits_cat = Category.objects.get(name='Tropical Fruits')
        
        sample_products = [
            {
                'name': 'Fresh Spinach',
                'category': vegetables_cat,
                'description': 'Fresh organic spinach leaves, perfect for salads and cooking.',
                'base_price': 25.00,
                'points': 5,
            },
            {
                'name': 'Sweet Mango',
                'category': fruits_cat,
                'description': 'Sweet tropical mango, rich in vitamins and perfect for desserts.',
                'base_price': 45.00,
                'points': 8,
            },
        ]
        
        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            
            if created:
                # Create package options for each product
                package_options = [
                    ('small', '250g', product_data['base_price'] * 0.8),
                    ('medium', '500g', product_data['base_price']),
                    ('large', '1kg', product_data['base_price'] * 1.8),
                    ('extra_large', '2kg', product_data['base_price'] * 3.5),
                    ('family_pack', '5kg', product_data['base_price'] * 8),
                ]
                
                for package_type, weight, price in package_options:
                    ProductOption.objects.create(
                        product=product,
                        package_type=package_type,
                        weight=weight,
                        price=price,
                        stock_quantity=50
                    )
        
        self.stdout.write(self.style.SUCCESS('Initial data setup completed'))
