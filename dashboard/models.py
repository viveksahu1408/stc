# dashboard/models.py
from django.db import models
from django.utils import timezone

class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    village_or_area = models.CharField(max_length=100)
    buying_frequency_days = models.IntegerField(default=15)
    default_rate_kati = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_rate_khadi = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.village_or_area})"

# ==========================================
# NEW INVENTORY STRUCTURE (DYNAMIC BRANDS)
# ==========================================
class ProductInventory(models.Model):
    CATEGORY_CHOICES = [
        ('KATI', 'Kati Supari'),
        ('KHADI', 'Khadi Supari'),
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    variety_name = models.CharField(max_length=50, default='Normal') # e.g., 'Jaam', 'Vachraj', 'Mora Moti', 'Kati'
    brand_name = models.CharField(max_length=50, default='No Brand') # e.g., 'Archana', 'Hina', 'STC'
    
    available_stock_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_purchase_rate_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Profit nikalne ke liye cost price

    class Meta:
        unique_together = ('category', 'variety_name', 'brand_name')

    def __str__(self):
        return f"{self.get_category_display()} - {self.variety_name} ({self.brand_name})"


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('CREDIT', 'Udhari'),
        ('PARTIAL', 'Partial'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    # Ab order direct product inventory se connect hoga
    product_item = models.ForeignKey(ProductInventory, on_delete=models.PROTECT, null=True)
    
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='CASH')
    # payment_mode = models.CharField(max_digits=10, choices=PAYMENT_CHOICES, default='CASH')
    date = models.DateField(default=timezone.now)
    promise_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity_kg * self.rate_per_kg
        self.amount_due = self.total_amount - self.amount_paid
        
        # Automatic Stock Reduction Logic
        if self.product_item:
            # Agar naya order hai (ID nahi hai), toh stock minus karo
            if not self.id:
                self.product_item.available_stock_kg -= self.quantity_kg
                self.product_item.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.customer.name}"


class PaymentLedger(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount_received = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True, null=True)