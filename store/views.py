from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.db.models import Sum
from django.utils import timezone
import razorpay
from .models import ( Product, Category, Cart, Order, Wishlist, Review, )
from .forms import ( ProductForm, CategoryForm, )
from django.views.decorators.csrf import csrf_exempt
from .models import ContactMessage

client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)

@csrf_exempt
def payment_success(request):

    if request.method != "POST":
        return HttpResponse("Invalid Request")

    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    params_dict = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }

    try:
        client.utility.verify_payment_signature(params_dict)

    except:
        messages.error(request, "Payment Verification Failed.")
        return redirect("checkout")

    cart_items = Cart.objects.filter(user=request.user)

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    order = Order.objects.create(
        user=request.user,
        full_name=request.session.get("checkout_name"),
        phone=request.session.get("checkout_phone"),
        address=request.session.get("checkout_address"),
        total_amount=total,
        status="Pending",
        payment_method="Razorpay",
        payment_status="Success",
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
        paid_at=timezone.now(),
    )

    # Reduce Product Stock
    for item in cart_items:
        if item.product.stock >= item.quantity:
            item.product.stock -= item.quantity
            item.product.save()

    subject = f"Payment Successful - Order #{order.id}"

    message = f"""
Hello {request.user.username},

Your payment has been received successfully.

Order ID : {order.id}

Amount : ₹{total}

Payment Method : Razorpay

Order Status : Pending

Thank you for shopping with Mithila Pride ❤️
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
        fail_silently=False,
    )

    cart_items.delete()

    messages.success(
        request,
        "Payment Successful."
    )

    return redirect("my_orders")
@csrf_exempt
def payment_failed(request):
    return HttpResponse("Payment Failed")

# =====================================
# HOME
# =====================================

def home(request):

    products = Product.objects.all().order_by("-id")
    categories = Category.objects.all()

    # Search
    search = request.GET.get("search")
    if search:
        products = products.filter(name__icontains=search)

    # Category Filter
    category = request.GET.get("category")
    if category:
        products = products.filter(category_id=category)

    # Price Filter
    max_price = request.GET.get("price")
    if max_price:
        products = products.filter(price__lte=max_price)

    paginator = Paginator(products, 8)
    page = request.GET.get("page")
    products = paginator.get_page(page)

    context = {
        "products": products,
        "categories": categories,
    }

    return render(request, "home.html", context)

# =====================================
# SEARCH
# =====================================

def search(request):

    query = request.GET.get("q")

    if query:
        products = Product.objects.filter(
            name__icontains=query
        )
    else:
        products = Product.objects.all()

    return render(
        request,
        "search.html",
        {
            "products": products,
            "query": query,
        },
    )


# =====================================
# CATEGORY
# =====================================

def category_products(request, id):

    category = get_object_or_404(
        Category,
        id=id
    )

    products = Product.objects.filter(
        category=category
    )

    return render(
        request,
        "category_products.html",
        {
            "category": category,
            "products": products,
        },
    )

# =====================================
# PRODUCT DETAIL
# =====================================

def product_detail(request, id):

    product = get_object_or_404(Product, id=id)

    reviews = Review.objects.filter(
        product=product
    ).order_by("-created_at")

    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    return render(
        request,
        "product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "related_products": related_products,
        },
    )

# =====================================
# REVIEW
# =====================================

@login_required
def add_review(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    # Check if user has a Delivered order
    delivered = Order.objects.filter(
        user=request.user,
        status="Delivered"
    ).exists()

    if not delivered:
        messages.error(
            request,
            "You can review only after your order is Delivered."
        )
        return redirect("product_detail", id=id)

    if request.method == "POST":

        rating = request.POST.get("rating")
        review_text = request.POST.get("review")

        # Update existing review or create new one
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                "rating": rating,
                "review": review_text,
            }
        )

        messages.success(
            request,
            "Your review has been saved successfully ⭐"
        )

    return redirect(
        "product_detail",
        id=id
    )
# =====================================
# ADD to cart
# =====================================

@login_required
def add_to_cart(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    # Product Out of Stock
    if product.stock <= 0:
        messages.error(
            request,
            "❌ This product is currently Out of Stock."
        )
        return redirect("product_detail", id=id)

    cart_item = Cart.objects.filter(
        user=request.user,
        product=product
    ).first()

    if cart_item:

        # Stock Limit Check
        if cart_item.quantity >= product.stock:
            messages.warning(
                request,
                f"Only {product.stock} item(s) available in stock."
            )
            return redirect("cart")

        cart_item.quantity += 1
        cart_item.save()

    else:

        Cart.objects.create(
            user=request.user,
            product=product,
            quantity=1,
        )

    messages.success(
        request,
        "🛒 Product added to cart."
    )

    return redirect("cart")

# =====================================
# CART
# =====================================

@login_required
def cart(request):

    cart_items = Cart.objects.filter(
        user=request.user
    )

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    return render(
        request,
        "cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
    )


# =====================================
# REMOVE CART ITEM
# =====================================

@login_required
def remove_from_cart(request, id):

    item = get_object_or_404(
        Cart,
        id=id,
        user=request.user
    )

    item.delete()

    messages.success(
        request,
        "Product removed from cart."
    )

    return redirect("cart")


# =====================================
# INCREASE QUANTITY
# =====================================
@login_required
def increase_quantity(request, id):

    item = get_object_or_404(
        Cart,
        id=id,
        user=request.user
    )

    if item.quantity >= item.product.stock:

        messages.warning(
            request,
            f"Only {item.product.stock} item(s) available."
        )

        return redirect("cart")

    item.quantity += 1
    item.save()

    return redirect("cart")

# =====================================
# DECREASE QUANTITY
# =====================================

@login_required
def decrease_quantity(request, id):

    item = get_object_or_404(
        Cart,
        id=id,
        user=request.user
    )

    if item.quantity > 1:

        item.quantity -= 1
        item.save()

    else:

        item.delete()

    return redirect("cart")


# =====================================
# SIGNUP
# =====================================

def signup(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("signup")

        User.objects.create_user(

            username=username,

            email=email,

            password=password,

        )

        messages.success(
            request,
            "Account created successfully."
        )

        return redirect("login")

    return render(
        request,
        "signup.html"
    )


# =====================================
# LOGIN
# =====================================

def login_user(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(

            request,

            username=username,

            password=password,

        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                "Login Successful"
            )

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid Username or Password"
            )

    return render(
        request,
        "login.html"
    )


# =====================================
# LOGOUT
# =====================================

@login_required
def logout_user(request):

    logout(request)

    messages.success(
        request,
        "Logout Successful"
    )

    return redirect("home")


# =====================================
# PROFILE
# =====================================

@login_required
def profile(request):

    return render(
        request,
        "profile.html"
    )

# =====================================
# CHECKOUT
# =====================================

@login_required
def checkout(request):

    cart_items = Cart.objects.filter(user=request.user)

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    if total == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        #amount = int(total * 100)
        amount = 1000

        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        request.session["checkout_name"] = name
        request.session["checkout_phone"] = phone
        request.session["checkout_address"] = address

        context = {
            "cart_items": cart_items,
            "total": total,
            "razorpay_order_id": razorpay_order["id"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": amount,
            "name": name,
            "phone": phone,
            "address": address,
        }

        return render(request, "checkout.html", context)

    return render(
        request,
        "checkout.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
    )
# =====================================
# MY ORDERS
# =====================================

@login_required
def my_orders(request):

    orders = Order.objects.filter(

        user=request.user

    ).order_by(

        "-created_at"

    )

    return render(
    request,
    "my_orders.html",
    {
        "orders": orders
    }
)
# =====================================
# WISHLIST
# =====================================

@login_required
def add_to_wishlist(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    messages.success(
        request,
        "Added to Wishlist ❤️"
    )

    return redirect("wishlist")


@login_required
def wishlist(request):

    items = Wishlist.objects.filter(
        user=request.user
    )

    return render(
        request,
        "wishlist.html",
        {
            "items": items
        }
    )


@login_required
def remove_wishlist(request, id):

    item = get_object_or_404(
        Wishlist,
        id=id,
        user=request.user
    )

    item.delete()

    messages.success(
        request,
        "Removed from Wishlist."
    )

    return redirect("wishlist")


# =====================================
# SELLER DASHBOARD
# =====================================


@login_required
def dashboard(request):

    products = Product.objects.count()
    orders = Order.objects.count()
    users = User.objects.count()
    reviews = Review.objects.count()
    wishlist = Wishlist.objects.count()

    revenue = Order.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    recent_orders = Order.objects.order_by("-created_at")[:5]

    context = {
        "products": products,
        "orders": orders,
        "users": users,
        "reviews": reviews,
        "wishlist": wishlist,
        "revenue": revenue,
        "recent_orders": recent_orders,
    }

    return render(
        request,
        "dashboard.html",
        context
    )


# =====================================
# ADD PRODUCT
# =====================================

@login_required
def add_product(request):

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Product Added Successfully."
            )

            return redirect("manage_products")

    else:

        form = ProductForm()

    return render(
        request,
        "add_product.html",
        {
            "form": form
        }
    )


# =====================================
# MANAGE PRODUCTS
# =====================================

@login_required
def manage_products(request):

    products = Product.objects.all().order_by(
        "-id"
    )

    return render(
        request,
        "manage_products.html",
        {
            "products": products
        }
    )


# =====================================
# EDIT PRODUCT
# =====================================

@login_required
def edit_product(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Product Updated Successfully."
            )

            return redirect(
                "manage_products"
            )

    else:

        form = ProductForm(
            instance=product
        )

    return render(
        request,
        "edit_product.html",
        {
            "form": form
        }
    )


# =====================================
# DELETE PRODUCT
# =====================================

@login_required
def delete_product(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    product.delete()

    messages.success(
        request,
        "Product Deleted Successfully."
    )

    return redirect(
        "manage_products"
    )

# =====================================
# MANAGE CATEGORIES
# =====================================

@login_required
def manage_categories(request):

    categories = Category.objects.all().order_by("-id")

    return render(
        request,
        "manage_categories.html",
        {
            "categories": categories
        }
    )


# =====================================
# ADD CATEGORY
# =====================================

@login_required
def add_category(request):

    if request.method == "POST":

        form = CategoryForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Category Added Successfully."
            )

            return redirect(
                "manage_categories"
            )

    else:

        form = CategoryForm()

    return render(
        request,
        "add_category.html",
        {
            "form": form
        }
    )


# =====================================
# EDIT CATEGORY
# =====================================

@login_required
def edit_category(request, id):

    category = get_object_or_404(
        Category,
        id=id
    )

    if request.method == "POST":

        form = CategoryForm(
            request.POST,
            request.FILES,
            instance=category
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Category Updated Successfully."
            )

            return redirect(
                "manage_categories"
            )

    else:

        form = CategoryForm(
            instance=category
        )

    return render(
        request,
        "edit_category.html",
        {
            "form": form
        }
    )


# =====================================
# DELETE CATEGORY
# =====================================

@login_required
def delete_category(request, id):

    category = get_object_or_404(
        Category,
        id=id
    )

    category.delete()

    messages.success(
        request,
        "Category Deleted Successfully."
    )

    return redirect(
        "manage_categories"
    )


# =====================================
# MANAGE ORDERS
# =====================================

@login_required
def manage_orders(request):

    orders = Order.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "manage_orders.html",
        {
            "orders": orders
        }
    )


# =====================================
# SALES ANALYTICS
# =====================================

@login_required
def analytics(request):

    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_reviews = Review.objects.count()
    total_wishlist = Wishlist.objects.count()

    revenue = sum(
        order.total_amount
        for order in Order.objects.all()
    )

    context = {

        "products": total_products,

        "orders": total_orders,

        "users": total_users,

        "reviews": total_reviews,

        "wishlist": total_wishlist,

        "revenue": revenue,

    }

    return render(
        request,
        "analytics.html",
        context
    )

def test_email(request):
    send_mail(
        "Test Email",
        "Congratulations! Email setup is working.",
        settings.DEFAULT_FROM_EMAIL,
        ["mansi11411@gmail.com"],   # Yahan test email
        fail_silently=False,
    )
    return HttpResponse("Email Sent Successfully!")

@login_required
def download_invoice(request, id):

    order = get_object_or_404(
        Order,
        id=id,
        user=request.user
    )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="Invoice_{order.id}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 800, "Mithila Pride")

    p.setFont("Helvetica", 14)
    p.drawString(50, 760, f"Invoice No : {order.id}")
    p.drawString(50, 735, f"Customer : {order.full_name}")
    p.drawString(50, 710, f"Phone : {order.phone}")
    p.drawString(50, 685, f"Address : {order.address}")

    p.drawString(50, 640, f"Order Status : {order.status}")

    p.drawString(50, 615, f"Total Amount : ₹{order.total_amount}")

    p.drawString(
        50,
        560,
        "Thank you for shopping with Mithila Pride ❤️"
    )

    p.showPage()
    p.save()

    return response

@login_required
def update_order_status(request, id, status):

    order = get_object_or_404(Order, id=id)

    order.status = status

    order.save()

    # Email Subject
    subject = f"Order #{order.id} Status Updated"

    # Email Message
    message = f"""
Hello {order.full_name},

Your Mithila Pride order status has been updated.

📦 Order ID : {order.id}

🚚 New Status : {status}

Payment Status : {order.payment_status}

Thank you for shopping with Mithila Pride ❤️
"""

    # Send Email
    if order.user.email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=True,
        )

    messages.success(
        request,
        f"Order #{order.id} updated to {status}."
    )

    return redirect("manage_orders")

@login_required
def buy_now(request, id):

    product = get_object_or_404(Product, id=id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("checkout")

# =====================================
# CONTACT US
# =====================================

def contact(request):

    if request.method == "POST":

        ContactMessage.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            subject=request.POST.get("subject"),
            message=request.POST.get("message"),
        )

        # Admin ko email
        send_mail(
            request.POST.get("subject"),
            f"""
Name: {request.POST.get("name")}

Email: {request.POST.get("email")}

Message:
{request.POST.get("message")}
""",
            settings.DEFAULT_FROM_EMAIL,
            ["mithilaprideindia@gmail.com"],
            fail_silently=False,
        )

        messages.success(
            request,
            "Your message has been sent successfully."
        )

        return redirect("contact")

    return render(
        request,
        "contact.html"
    )