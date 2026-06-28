# dashboard/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 🌍 Main Public Website (No login needed - Sabko dikhegi)
    path('', views.landing_page, name='landing_page'),

    # 🔒 Secure Internal Dashboard (Sirf Login ke baad khulega)
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    
    # 📦 Business Management Routes
    path('new-sale/', views.create_sale, name='create_sale'), 
    path('add-customer/', views.add_customer, name='add_customer'), 
    path('add-stock/', views.add_stock, name='add_stock'), 
    path('collection-tracker/', views.collection_tracker, name='collection_tracker'),

    # 📖 Ledger & Accounts Routes
    path('ledger/', views.customer_ledger_list, name='ledger_list'), 
    path('ledger/collect/<int:customer_id>/', views.collect_payment, name='collect_payment'), 
    path('reports/', views.advance_reports, name='advance_reports'),

    # 🔐 Authentication System (Login / Logout)
    path('login/', auth_views.LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing_page'), name='logout'),
]