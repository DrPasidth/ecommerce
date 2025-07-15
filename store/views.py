## store/views.py
```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from .models import *
from accounts.models import UserProfile, PointsHistory
import json

def index(request):
    carousel_images = CarouselImage.objects.filter(is_active=True)[:5]
    vegetables = Product.objects.filter(category__category_type='vegetable', is_active=True)
    fruits = Product.objects.filter(category__category_type='fruit', is_active=True)
    others = Product.objects.filter(category__category_type='other', is_active=True)
    
    # Get active promotions
    active_promotions = ProductPromotion.objects.filter(
        promotion__is_active=True,
        promotion__start_date__lte=timezone.now(),
        promotion__end_date__gte=timezone.now()
    )
    
    context = {
        'carousel_images': carousel_images,
        'vegetables': vegetables,
        'fruits': fruits,
        'others': others,
        'active_promotions': active_promotions,
    }
    return render(request, 'store/index.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    options = product.options.all()
    
    # Check for active promotions
    promotion = ProductPromotion.objects.filter(
        product=product,
        promotion__is_active=True,
        promotion__start_date__lte=timezone.now(),
        promotion__end_date__gte=timezone.now()
    ).first()
    
    context = {
        'product': product,
        'options': options,
        'promotion': promotion,
    }
    return render(request, 'store/product_detail.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_option_id = request.POST.get('product_option_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product_option = get_object_or_404(ProductOption, id=product_option_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_option=product_option,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, 'Item added to cart successfully!')
        return redirect('cart')

@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total = sum(item.get_total_price() for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'store/cart.html', context)

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty!')
        return redirect('cart')
    
    subtotal = sum(item.get_total_price() for item in cart_items)
    user_profile = request.user.userprofile
    available_points = user_profile.points
    
    # Calculate maximum points discount
    settings = SiteSettings.objects.first()
    if settings:
        max_points_discount = available_points * settings.points_to_currency_rate
    else:
        max_points_discount = available_points * 0.10  # Default rate
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'available_points': available_points,
        'max_points_discount': max_points_discount,
    }
    return render(request, 'store/checkout.html', context)

@login_required
def process_checkout(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items:
            messages.error(request, 'Your cart is empty!')
            return redirect('cart')
        
        subtotal = sum(item.get_total_price() for item in cart_items)
        points_to_use = int(request.POST.get('points_to_use', 0))
        
        # Calculate points discount
        settings = SiteSettings.objects.first()
        points_rate = settings.points_to_currency_rate if settings else 0.10
        points_discount = min(points_to_use * points_rate, subtotal)
        
        total_amount = subtotal - points_discount
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            points_used=points_to_use,
            points_discount=points_discount
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_option=cart_item.product_option,
                quantity=cart_item.quantity,
                price=cart_item.product_option.price
            )
        
        # Update user points
        user_profile = request.user.userprofile
        if points_to_use > 0:
            user_profile.points -= points_to_use
            PointsHistory.objects.create(
                user=request.user,
                transaction_type='redeemed',
                points=points_to_use,
                description=f'Redeemed for order {order.order_number}'
            )
        
        # Add points for purchase
        earned_points = sum(item.product_option.product.points * item.quantity for item in cart_items)
        user_profile.points += earned_points
        user_profile.save()
        
        PointsHistory.objects.create(
            user=request.user,
            transaction_type='earned',
            points=earned_points,
            description=f'Earned from order {order.order_number}'
        )
        
        # Clear cart
        cart.items.all().delete()
        
        return redirect('payment', order_id=order.id)

@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    settings = SiteSettings.objects.first()
    
    context = {
        'order': order,
        'settings': settings,
    }
    return render(request, 'store/payment.html', context)

@csrf_exempt
def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = data.get('quantity')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'success': True,
                'new_total': float(cart_item.get_total_price())
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart')
  
