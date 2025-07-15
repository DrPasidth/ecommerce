## store/models.py
```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('vegetable', 'Vegetables'),
        ('fruit', 'Fruits'),
        ('other', 'Others'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    points = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ProductOption(models.Model):
    PACKAGE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large'),
        ('family_pack', 'Family Pack'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='options')
    package_type = models.CharField(max_length=20, choices=PACKAGE_CHOICES)
    weight = models.CharField(max_length=50)  # e.g., "500g", "1kg"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.product.name} - {self.package_type} ({self.weight})"

class Promotion(models.Model):
    name = models.CharField(max_length=200)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    tag_text = models.CharField(max_length=50, default="SALE")
    
    def __str__(self):
        return self.name

class ProductPromotion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)
    promotional_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} - {self.promotion.name}"

class CarouselImage(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='carousel/')
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_option = models.ForeignKey(ProductOption, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    def get_total_price(self):
        return self.product_option.price * self.quantity

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    points_used = models.IntegerField(default=0)
    points_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
        
        # Generate QR code
        if not self.qr_code:
            qr_data = f"Order: {self.order_number}\nAmount: {self.total_amount} THB\nDate: {self.created_at.strftime('%Y-%m-%d %H:%M')}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            file_name = f'qr_{self.order_number}.png'
            self.qr_code.save(file_name, File(buffer), save=False)
            super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_option = models.ForeignKey(ProductOption, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_total_price(self):
        return self.price * self.quantity

class SiteSettings(models.Model):
    company_name = models.CharField(max_length=200, default="Fresh Market")
    bank_account_name = models.CharField(max_length=200)
    bank_account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    points_to_currency_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.10)  # 100 points = 10 baht
    referral_points = models.IntegerField(default=50)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.company_name
