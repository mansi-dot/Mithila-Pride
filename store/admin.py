from django.contrib import admin
from .models import (Product,Category,Cart,Order,Review,Wishlist,ContactMessage,)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Wishlist)
admin.site.register(Review)
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "subject",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "subject",
    )

    list_filter = (
        "created_at",
    )
    ordering = (
        "-created_at",
    )