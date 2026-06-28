# dashboard/admin.py
# from .models import Customer, ProductStock, Order, PaymentLedger
# dashboard/admin.py
from django.contrib import admin
from .models import Customer, ProductInventory, Order, PaymentLedger

admin.site.register(Customer)
admin.site.register(ProductInventory)
admin.site.register(Order)
admin.site.register(PaymentLedger)