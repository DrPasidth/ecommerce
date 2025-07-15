## store/urls.py
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]
