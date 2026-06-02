from django.db import models

# Create your models here.
class Customer(models.Model):
    username = models.CharField(max_length = 20)
    password = models.CharField(max_length = 20)
    email = models.CharField(max_length = 20)
    mobile = models.CharField(max_length = 10)
    address = models.CharField(max_length = 50)

class Restaurant(models.Model):
    name = models.CharField(max_length = 20)
    picture = models.URLField(max_length = 200, default='https://designshack.net/wp-content/uploads/Free-Simple-Restaurant-Logo-Template.jpg')
    cuisine = models.CharField(max_length = 200)
    rating = models.FloatField()
    
class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete = models.CASCADE, related_name = "items")
    name = models.CharField(max_length = 20)
    description = models.CharField(max_length = 200)
    price = models.FloatField()
    vegeterian = models.BooleanField(default=False)
    picture = models.URLField(max_length = 400, default='https://www.indiafilings.com/learn/wp-content/uploads/2024/08/How-to-Start-Food-Business.jpg')

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE, related_name = "cart")
    items = models.ManyToManyField("Item", related_name = "carts")

    def total_price(self):
        cart_items = self.cart_items.select_related("item").all()
        cart_item_ids = [cart_item.item_id for cart_item in cart_items]
        cart_item_total = sum(cart_item.line_total() for cart_item in cart_items)
        legacy_total = sum(item.price for item in self.items.exclude(id__in = cart_item_ids))
        return cart_item_total + legacy_total
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete = models.CASCADE, related_name = "cart_items")
    item = models.ForeignKey(Item, on_delete = models.CASCADE)
    quantity = models.PositiveIntegerField(default = 1)

    class Meta:
        unique_together = ("cart", "item")

    def line_total(self):
        return self.item.price * self.quantity

class CustomerOrder(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE, related_name = "orders")
    payment_method = models.CharField(max_length = 40)
    delivery_address = models.CharField(max_length = 200)
    total_price = models.FloatField()
    status = models.CharField(max_length = 30, default = "Placed")
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"

class CustomerOrderItem(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete = models.CASCADE, related_name = "items")
    item_name = models.CharField(max_length = 100)
    restaurant_name = models.CharField(max_length = 100)
    unit_price = models.FloatField()
    quantity = models.PositiveIntegerField(default = 1)
    line_total = models.FloatField()
    
