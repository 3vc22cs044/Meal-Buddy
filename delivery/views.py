from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Customer, Restaurant, Item, Cart, CartItem, CustomerOrder, CustomerOrderItem

import razorpay
from django.conf import settings

# Create your views here.
def index(request):
    return render(request, 'delivery/index.html')

def open_signin(request):
    return render(request, 'delivery/signin.html')

def open_signup(request):
    return render(request, 'delivery/signup.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        try:
            Customer.objects.get(username = username)
            return HttpResponse("Duplicate username!")
        except:
            Customer.objects.create(
                username = username,
                password = password,
                email = email,
                mobile = mobile,
                address = address,
            )
    return render(request, 'delivery/signin.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

    try:
        Customer.objects.get(username = username, password = password)
        if username == 'admin':
            return render(request, 'delivery/admin_home.html')
        else:
            restaurantList = Restaurant.objects.all()
            return render(request, 'delivery/customer_home.html',{"restaurantList" : restaurantList, "username" : username})

    except Customer.DoesNotExist:
        return render(request, 'delivery/fail.html')
    
def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')
        
        try:
            Restaurant.objects.get(name = name)
            return HttpResponse("Duplicate restaurant!")
        except:
            Restaurant.objects.create(
                name = name,
                picture = picture,
                cuisine = cuisine,
                rating = rating,
            )
    return render(request, 'delivery/admin_home.html')

def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList})

def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    return render(request, 'delivery/update_restaurant.html', {"restaurant" : restaurant})

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')
        
        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating

        restaurant.save()

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList})


def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    restaurant.delete()

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList})


def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #itemList = Item.objects.all()
    return render(request, 'delivery/update_menu.html',{"itemList" : itemList, "restaurant" : restaurant})
    
def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')
        
        try:
            Item.objects.get(name = name)
            return HttpResponse("Duplicate item!")
        except:
            Item.objects.create(
                restaurant = restaurant,
                name = name,
                description = description,
                price = price,
                vegeterian = vegeterian,
                picture = picture,
            )
    return render(request, 'delivery/admin_home.html')

def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #itemList = Item.objects.all()
    return render(request, 'delivery/customer_menu.html'
                  ,{"itemList" : itemList,
                     "restaurant" : restaurant, 
                     "username":username})

def cart_details(cart):
    if not cart:
        return [], 0

    cart_items = list(cart.cart_items.select_related("item").all())
    cart_item_ids = [cart_item.item_id for cart_item in cart_items]

    for item in cart.items.exclude(id__in = cart_item_ids):
        cart_items.append({
            "item": item,
            "quantity": 1,
            "line_total": item.price,
        })

    return cart_items, cart.total_price()

def add_item_to_cart(cart, item):
    already_in_legacy_cart = cart.items.filter(id = item.id).exists()
    cart_item, created = CartItem.objects.get_or_create(
        cart = cart,
        item = item,
        defaults = {"quantity": 1},
    )

    if created and already_in_legacy_cart:
        cart_item.quantity = 2
        cart_item.save()
    elif not created:
        cart_item.quantity += 1
        cart_item.save()

    cart.items.add(item)

def add_to_cart(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = Customer.objects.get(username = username)

    cart, created = Cart.objects.get_or_create(customer = customer)

    add_item_to_cart(cart, item)

    return HttpResponse('added to cart')

def show_cart(request, username):
    customer = Customer.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items, total_price = cart_details(cart)

    return render(request, 'delivery/cart.html',{"cartItems" : cart_items, "total_price" : total_price, "username":username})

def increase_cart_item(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = Customer.objects.get(username = username)
    cart, created = Cart.objects.get_or_create(customer = customer)

    add_item_to_cart(cart, item)

    cart_items, total_price = cart_details(cart)

    return render(request, 'delivery/cart.html',{"cartItems" : cart_items, "total_price" : total_price, "username":username})

def decrease_cart_item(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = Customer.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()

    if cart:
        cart_item = CartItem.objects.filter(cart = cart, item = item).first()
        if cart_item and cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            if cart_item:
                cart_item.delete()
            cart.items.remove(item)

    cart_items, total_price = cart_details(cart)

    return render(request, 'delivery/cart.html',{"cartItems" : cart_items, "total_price" : total_price, "username":username})

def remove_from_cart(request, item_id, username):
    customer = Customer.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()

    if cart:
        item = Item.objects.filter(id = item_id).first()
        if item:
            CartItem.objects.filter(cart = cart, item = item).delete()
            cart.items.remove(item)

    cart_items, total_price = cart_details(cart)

    return render(request, 'delivery/cart.html',{"cartItems" : cart_items, "total_price" : total_price, "username":username})

# Checkout View
def checkout(request, username):
    # Fetch customer and their cart
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items, total_price = cart_details(cart)

    if total_price == 0:
        return render(request, 'delivery/checkout.html', {
            'error': 'Your cart is empty!',
        })

    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    order_data = {
        'amount': int(total_price * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',  # Automatically capture payment
    }
    order = client.order.create(data=order_data)

    # Pass the order details to the frontend
    return render(request, 'delivery/checkout.html', {
        'username': username,
        'cartItems': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],  # Razorpay order ID
        'amount': total_price,
    })

def clear_cart(cart):
    if cart:
        cart.cart_items.all().delete()
        cart.items.clear()

def create_order_from_cart(customer, cart_items, total_price, payment_method):
    order = CustomerOrder.objects.create(
        customer = customer,
        payment_method = payment_method,
        delivery_address = customer.address,
        total_price = total_price,
    )

    for cart_item in cart_items:
        item = cart_item["item"] if isinstance(cart_item, dict) else cart_item.item
        quantity = cart_item["quantity"] if isinstance(cart_item, dict) else cart_item.quantity
        line_total = cart_item["line_total"] if isinstance(cart_item, dict) else cart_item.line_total()

        CustomerOrderItem.objects.create(
            order = order,
            item_name = item.name,
            restaurant_name = item.restaurant.name,
            unit_price = item.price,
            quantity = quantity,
            line_total = line_total,
        )

    return order

def cash_on_delivery(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items, total_price = cart_details(cart)

    if request.method != 'POST':
        return render(request, 'delivery/cart.html', {
            "cartItems": cart_items,
            "total_price": total_price,
            "username": username,
        })

    if total_price == 0:
        return render(request, 'delivery/checkout.html', {
            'error': 'Your cart is empty!',
            'username': username,
        })

    order = create_order_from_cart(customer, cart_items, total_price, 'Cash on Delivery')
    clear_cart(cart)

    return render(request, 'delivery/cash_on_delivery.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
        'payment_method': 'Cash on Delivery',
        'order': order,
    })


# Orders Page
def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    # Fetch cart items and total price before clearing the cart
    cart_items, total_price = cart_details(cart)
    if total_price:
        create_order_from_cart(customer, cart_items, total_price, 'Razorpay')

    # Clear the cart after fetching its details
    clear_cart(cart)

    return render(request, 'delivery/orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })

def my_orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    order_list = CustomerOrder.objects.filter(customer=customer).prefetch_related("items").order_by("-created_at")

    return render(request, 'delivery/my_orders.html', {
        'username': username,
        'customer': customer,
        'order_list': order_list,
    })
