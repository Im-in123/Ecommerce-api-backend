from django.contrib import admin
from .models import Inventory, InventoryGroup, Photo, Shop, Invoice, InvoiceItem, Size, Color


admin.site.register((Inventory, InventoryGroup, Shop,
                    Invoice, InvoiceItem, Photo, Size, Color,))
