# dashboard/views.py
from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal  # <-- 1. Sabse upar yeh naya import jodo!
from .models import Customer, ProductInventory, Order, PaymentLedger
from django.db.models import F, ExpressionWrapper, DecimalField
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views



def landing_page(request):
    return render(request, 'dashboard/landing_page.html')

@login_required
def dashboard_home(request):
    today = timezone.now().date()

    # 1. Aaj ki Kul Bikri (Total Sales amount from Orders)
    today_sales_amount = Order.objects.filter(date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # 2. Aaj ka mila hua kul cash (From Payment Ledger + Cash orders of today)
    ledger_cash = PaymentLedger.objects.filter(date=today).aggregate(Sum('amount_received'))['amount_received__sum'] or 0
    order_cash = Order.objects.filter(date=today, payment_mode='CASH').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_partial_cash = Order.objects.filter(date=today, payment_mode='PARTIAL').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    today_total_collection = ledger_cash + order_cash + order_partial_cash

    # 3. Market me Kul Pending Udhari
    total_market_udhari = Order.objects.aggregate(Sum('amount_due'))['amount_due__sum'] or 0

    # 4. LIVE STOCK BREAKDOWN (Naye ProductInventory Model ke hisab se)
    # Sabhi Kati aur Khadi categories ka total sum nikalenge
    stock_kati_kg = ProductInventory.objects.filter(category='KATI').aggregate(Sum('available_stock_kg'))['available_stock_kg__sum'] or 0
    stock_khadi_kg = ProductInventory.objects.filter(category='KHADI').aggregate(Sum('available_stock_kg'))['available_stock_kg__sum'] or 0

    # 5. PRIORITY COLLECTION PANEL (Kiska vada aaj ka hai aur udhari baqi hai)
    pending_collections = Order.objects.filter(amount_due__gt=0, promise_date__lte=today).order_by('promise_date')

    # 6. RETENTION ANALYTICS (Maal kab khatam hone wala hai - Predictive Logic)
    customers = Customer.objects.all()
    customers_to_reach = []

    for cust in customers:
        last_order = Order.objects.filter(customer=cust).order_by('-date').first()
        if not last_order:
            customers_to_reach.append({
                'customer': cust,
                'days_overdue': 'Naya Grahak'
            })
        else:
            days_since_last_order = (today - last_order.date).days
            if days_since_last_order >= cust.buying_frequency_days:
                overdue = days_since_last_order - cust.buying_frequency_days
                customers_to_reach.append({
                    'customer': cust,
                    'days_overdue': overdue
                })

    context = {
        'today_sales_amount': today_sales_amount,
        'today_total_collection': today_total_collection,
        'total_market_udhari': total_market_udhari,
        'stock_kati_kg': stock_kati_kg,
        'stock_khadi_kg': stock_khadi_kg,
        'pending_collections': pending_collections,
        'customers_to_reach': customers_to_reach,
    }
    return render(request, 'dashboard/home.html', context)
    pass
# dashboard/views.py me sabse niche add karo

# dashboard/views.py ke andar create_sale view ko replace karo
@login_required
def create_sale(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        # Frontend se ab seedhe Product Inventory row ki ID aayegi
        product_item_id = request.POST.get('product_item') 
        
        quantity_kg = Decimal(request.POST.get('quantity_kg') or '0')
        rate_per_kg = Decimal(request.POST.get('rate_per_kg') or '0')
        payment_mode = request.POST.get('payment_mode')
        amount_paid = Decimal(request.POST.get('amount_paid') or '0')
        promise_date = request.POST.get('promise_date') or None

        customer = Customer.objects.get(id=customer_id)
        product_item = ProductInventory.objects.get(id=product_item_id)
        
        # Naye structure ke hisab se order save hoga
        order = Order(
            customer=customer,
            product_item=product_item, # ID ki jagah poora object pass kiya
            quantity_kg=quantity_kg,
            rate_per_kg=rate_per_kg,
            payment_mode=payment_mode,
            amount_paid=amount_paid,
            promise_date=promise_date
        )
        order.save()

        return redirect('dashboard_home')

    # GET request me saare customers aur live inventory options nikalenge
    customers = Customer.objects.all().order_by('name')
    inventory_items = ProductInventory.objects.filter(available_stock_kg__gt=0).order_by('category', 'variety_name')
    
    return render(request, 'dashboard/create_sale.html', {
        'customers': customers,
        'inventory_items': inventory_items
    })
    pass

# dashboard/views.py me sabse niche add karo
@login_required
def add_customer(request):
    if request.method == 'POST':
        # Form ka data uthana
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        village_or_area = request.POST.get('village_or_area')
        buying_frequency_days = int(request.POST.get('buying_frequency_days') or 7)
        default_rate_kati = Decimal(request.POST.get('default_rate_kati') or '0')
        default_rate_khadi = Decimal(request.POST.get('default_rate_khadi') or '0')

        # Naya Customer save karna
        customer = Customer(
            name=name,
            phone_number=phone_number,
            village_or_area=village_or_area,
            buying_frequency_days=buying_frequency_days,
            default_rate_kati=default_rate_kati,
            default_rate_khadi=default_rate_khadi
        )
        customer.save()

        # Save hone ke baad seedhe Home Dashboard par bhej do
        return redirect('dashboard_home')

    return render(request, 'dashboard/add_customer.html')
    pass
# dashboard/views.py me sabse niche add karo
@login_required
def customer_ledger_list(request):
    # Saare customers ko uthayenge aur unka total udhari (amount_due) calculate karenge
    customers = Customer.objects.all().order_by('name')
    
    ledger_data = []
    for customer in customers:
        # Is customer ki total pending udhari sum karo
        total_due = Order.objects.filter(customer=customer).aggregate(Sum('amount_due'))['amount_due__sum'] or 0
        ledger_data.append({
            'customer': customer,
            'total_due': total_due
        })
        
    return render(request, 'dashboard/ledger_list.html', {'ledger_data': ledger_data})
    pass


@login_required
def collect_payment(request, customer_id):
    customer = Customer.objects.get(id=customer_id)
    
    if request.method == 'POST':
        amount_received = Decimal(request.POST.get('amount_received') or '0')
        remarks = request.POST.get('remarks') or ''
        
        # 1. Ledger table me transaction save karo
        payment = PaymentLedger(
            customer=customer,
            amount_received=amount_received,
            remarks=remarks
        )
        payment.save()
        
        # 2. DATA ANALYST MAGIC / LOGIC:
        # Jo paisa mila hai, use customer ke sabse purane udhari wale orders me se minus karte chalenge (FIFO Method)
        pending_orders = Order.objects.filter(customer=customer, amount_due__gt=0).order_by('date')
        
        remaining_payment = amount_received
        for order in pending_orders:
            if remaining_payment <= 0:
                break
                
            if order.amount_due <= remaining_payment:
                # Agar order ki udhari received payment se kam ya barabar hai
                remaining_payment -= order.amount_due
                order.amount_paid += order.amount_due
                order.amount_due = 0
            else:
                # Agar order ki udhari received payment se zyada hai
                order.amount_paid += remaining_payment
                order.amount_due -= remaining_payment
                remaining_payment = 0
                
            order.save() # Order table automatic update ho jayegi
            
        return redirect('ledger_list')
        
    total_due = Order.objects.filter(customer=customer).aggregate(Sum('amount_due'))['amount_due__sum'] or 0
    return render(request, 'dashboard/collect_payment.html', {'customer': customer, 'total_due': total_due})
    pass


@login_required
def advance_reports(request):
    orders = Order.objects.all().select_related('customer', 'product_item')
    
    # All Filter Options for Dropdowns
    all_villages = Customer.objects.values_list('village_or_area', flat=True).distinct().order_by('village_or_area')
    all_categories = ProductInventory.CATEGORY_CHOICES
    all_varieties = ProductInventory.objects.values_list('variety_name', flat=True).distinct().order_by('variety_name')
    all_brands = ProductInventory.objects.values_list('brand_name', flat=True).distinct().order_by('brand_name')

    # ==========================================
    # APPLY FILTERS DYNAMICALLY
    # ==========================================
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    village = request.GET.get('village')
    category = request.GET.get('category')
    variety = request.GET.get('variety')
    brand = request.GET.get('brand')

    if start_date and end_date:
        orders = orders.filter(date__range=[start_date, end_date])
    if village:
        orders = orders.filter(customer__village_or_area=village)
    if category:
        orders = orders.filter(product_item__category=category)
    if variety:
        orders = orders.filter(product_item__variety_name=variety)
    if brand:
        orders = orders.filter(product_item__brand_name=brand)

    # ==========================================
    # DATA ANALYTICS: TOTAL SALES & PROFIT
    # ==========================================
    total_filtered_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_filtered_qty = orders.aggregate(Sum('quantity_kg'))['quantity_kg__sum'] or 0
    
    # Calculate Profit: (Selling Rate - Purchase Cost Rate) * Quantity
    total_profit = 0
    for order in orders:
        if order.product_item:
            cost = order.product_item.avg_purchase_rate_per_kg * order.quantity_kg
            profit = order.total_amount - cost
            total_profit += profit

    # Live Detailed Stock Status for Table
    live_stock = ProductInventory.objects.all().order_by('category', 'variety_name')

    context = {
        'orders': orders,
        'all_villages': all_villages,
        'all_categories': all_categories,
        'all_varieties': all_varieties,
        'all_brands': all_brands,
        'total_filtered_sales': total_filtered_sales,
        'total_filtered_qty': total_filtered_qty,
        'total_profit': total_profit,
        'live_stock': live_stock,
        # Selected values back to UI
        'selected_start': start_date,
        'selected_end': end_date,
        'selected_village': village,
        'selected_category': category,
        'selected_variety': variety,
        'selected_brand': brand,
    }
    return render(request, 'dashboard/advance_reports.html', context)
    pass
# dashboard/views.py me sabse niche add karo
@login_required
def add_stock(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        variety_name = request.POST.get('variety_name').strip()
        brand_name = request.POST.get('brand_name').strip() or 'No Brand'
        
        quantity_kg = Decimal(request.POST.get('quantity_kg') or '0')
        purchase_rate = Decimal(request.POST.get('purchase_rate') or '0')

        # DATA ANALYST MAGIC: Agar ye brand aur variety pehle se h, toh usi me plus karo
        # Agar naya h, toh naya row banao (get_or_create)
        product, created = ProductInventory.objects.get_or_create(
            category=category,
            variety_name=variety_name,
            brand_name=brand_name,
            defaults={
                'available_stock_kg': quantity_kg,
                'avg_purchase_rate_per_kg': purchase_rate
            }
        )

        if not created:
            # Purana stock aur naya stock mila kar average rate calculate karna
            total_qty = product.available_stock_kg + quantity_kg
            if total_qty > 0:
                # Weighted Average Cost Price formula taaki profit sahi nikle
                new_avg_rate = ((product.available_stock_kg * product.avg_purchase_rate_per_kg) + (quantity_kg * purchase_rate)) / total_qty
                product.avg_purchase_rate_per_kg = new_avg_rate
            
            product.available_stock_kg += quantity_kg
            product.save()

        # Stock save hone ke baad seedhe Advance Reports par bhej do jahan poora stock dikhta h
        return redirect('advance_reports')

    return render(request, 'dashboard/add_stock.html')
    pass
@login_required
def collection_tracker(request):
    # Sirf wahi orders nikalenge jinki udhari baqi hai (amount_due > 0)
    # Aur inko aane wali tarikh (promise_date) ke hisab se ascending order me sort karenge
    orders = Order.objects.filter(amount_due__gt=0).order_by('promise_date')

    # 1. LIVE SEARCH: Agar name query aayi hai
    search_query = request.GET.get('search', '').strip()
    if search_query:
        orders = orders.filter(customer__name__icontains=search_query)

    # 2. LOCATION FILTER: Agar gaon/area select kiya hai
    location_filter = request.GET.get('location', '').strip()
    if location_filter:
        orders = orders.filter(customer__village_or_area=location_filter)

    # Dropdown me dikhane ke liye un sabhi gaon ki list jahan udhari pending h
    active_locations = Customer.objects.filter(order__amount_due__gt=0).values_list('village_or_area', flat=True).distinct()

    context = {
        'orders': orders,
        'active_locations': active_locations,
        'search_query': search_query,
        'selected_location': location_filter,
    }
    return render(request, 'dashboard/collection_tracker.html', context)
    pass