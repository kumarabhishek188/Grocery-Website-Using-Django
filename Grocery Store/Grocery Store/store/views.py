from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Product, CartItem
from django.shortcuts import redirect
from django.http import HttpResponse
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))  # Default quantity to 1 if not provided

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return redirect('cart')

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.quantity * item.product.price_per_kg for item in cart_items)
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total_price': total_price})

def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)  # Adjust based on your user model
    total_price = sum(item.product.price_per_kg * item.quantity for item in cart_items)
    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def order_summary(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'shop/order_summary.html', {'order': order})

def process_payment(request):
    if request.method == 'POST':
        cart_items = CartItem.objects.filter(user=request.user)
        total_price = sum(item.product.price_per_kg * item.quantity for item in cart_items)
        
        # Simulate successful payment
        if request.POST.get('payment_success', True):  # Replace with actual payment check logic
            return redirect(reverse('payment_success'))
    
    return redirect(reverse('checkout'))

def generate_invoice(user, cart_items, total_price):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "Invoice")
    p.drawString(100, 730, f"User: {user.username}")
    
    y = 700
    for item in cart_items:
        p.drawString(100, y, f"{item.product.name} - {item.quantity} x ₹{item.product.price_per_kg} = ₹{item.quantity * item.product.price_per_kg}")
        y -= 20
    
    p.drawString(100, y, f"Total: ₹{total_price}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def payment_success(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.product.price_per_kg * item.quantity for item in cart_items)
    
    # Generate invoice
    invoice_buffer = generate_invoice(request.user, cart_items, total_price)
    CartItem.objects.filter(user=request.user).delete()
    
    # Return invoice as PDF
    response = HttpResponse(invoice_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    return response




