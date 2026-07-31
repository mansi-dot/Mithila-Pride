from django.urls import path
from . import views

urlpatterns = [

    # ==========================
    # HOME
    # ==========================
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),

    # ==========================
    # CATEGORY
    # ==========================
    path('category/<int:id>/', views.category_products, name='category_products'),

    # ==========================
    # PRODUCT
    # ==========================
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('review/<int:id>/', views.add_review, name='add_review'),

    # ==========================
    # CART
    # ==========================
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase/<int:id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:id>/', views.decrease_quantity, name='decrease_quantity'),

    # ==========================
    # WISHLIST
    # ==========================
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:id>/', views.remove_wishlist, name='remove_wishlist'),

    # ==========================
    # USER
    # ==========================
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),

    # ==========================
    # ORDER
    # ==========================
    path('checkout/', views.checkout, name='checkout'),
    path("payment-success/", views.payment_success, name="payment_success"),
   # path( "payment-failed/", views.payment_failed,name="payment_failed"),
    path('orders/', views.my_orders, name='my_orders'),

    # ==========================
    # SELLER DASHBOARD
    # ==========================
    path('dashboard/', views.dashboard, name='dashboard'),

    # Products
    path('dashboard/add-product/', views.add_product, name='add_product'),
    path('dashboard/manage-products/', views.manage_products, name='manage_products'),
    path('dashboard/edit-product/<int:id>/', views.edit_product, name='edit_product'),
    path('dashboard/delete-product/<int:id>/', views.delete_product, name='delete_product'),

    # Categories
    path('dashboard/manage-categories/', views.manage_categories, name='manage_categories'),
    path('dashboard/add-category/', views.add_category, name='add_category'),
    path('dashboard/edit-category/<int:id>/', views.edit_category, name='edit_category'),
    path('dashboard/delete-category/<int:id>/', views.delete_category, name='delete_category'),

    # Orders
    path('dashboard/manage-orders/', views.manage_orders, name='manage_orders'),

    # Analytics
    path('dashboard/analytics/', views.analytics, name='analytics'),

    path( "dashboard/update-order/<int:id>/", views.update_order_status, name="update_order_status"),

    path("test-email/", views.test_email, name="test_email"),

    path("invoice/<int:id>/",views.download_invoice,name="download_invoice"),

    path('dashboard/update-order/<int:id>/<str:status>/',views.update_order_status,name='update_order_status'),

    path('buy-now/<int:id>/',views.buy_now,name='buy_now'),

    path( "contact/",views.contact,name="contact"),
]
