from email.policy import default
import string
import random
from django.db import models
from user_controller.models import CustomUser
from user_controller.views import add_user_activity
from django.utils.text import slugify
from pyuploadcare.dj.models import ImageField
from tinymce.models import HTMLField


class InventoryGroup(models.Model):
    created_by = models.ForeignKey(
        CustomUser, null=True, related_name="inventory_groups",
        on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(default="", editable=True,
                            max_length=255, blank=True)
    belongs_to = models.ForeignKey(
        'self', null=True, on_delete=models.SET_NULL, related_name="group_relations", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_name = self.name
        self.slug = slugify(self.name, allow_unicode=True)

    def save(self, *args, **kwargs):

        action = f"added new group - '{self.name}'"
        if self.pk is not None:
            action = f"updated group from - '{self.old_name}' to '{self.name}'"
        super().save(*args, **kwargs)
        add_user_activity(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted group - '{self.name}'"
        super().delete(*args, **kwargs)
        add_user_activity(created_by, action=action)

    def __str__(self):
        return self.name


class Photo(models.Model):
    created_by = models.ForeignKey(
        CustomUser, null=True, related_name="inventory_photo_inner",
        on_delete=models.SET_NULL
    )
    image = models.ImageField(default="item.png", upload_to="inventory_photos")
    created_at = models.DateTimeField(auto_now_add=True)
    photo = ImageField(blank=True, manual_crop="", null=True)
    has_inv = models.BooleanField(default=False)


class Size(models.Model):
    name = models.CharField(unique=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(unique=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    created_by = models.ForeignKey(
        CustomUser, null=True, related_name="inventory_items",
        on_delete=models.SET_NULL
    )
    code = models.CharField(max_length=10, unique=True, null=True)
    # photo = models.TextField(blank=True, null=True)
    photo = models.ManyToManyField("Photo", related_name="inventory_photos")
    group = models.ForeignKey(
        InventoryGroup, related_name="inventories", null=True, on_delete=models.SET_NULL, blank=True
    )
    total = models.PositiveIntegerField()
    remaining = models.PositiveIntegerField(null=True)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(default="", editable=True,
                            max_length=255, blank=True)
    price = models.DecimalField(
        default=0,  max_digits=10,
        decimal_places=2)
    compare_price = models.DecimalField(
        default=0,  max_digits=10,
        decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = HTMLField(default="")
    sizes = models.ManyToManyField(Size, related_name="inventory_sizes")
    colors = models.ManyToManyField(Color, related_name="inventory_colors")

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.slug = slugify(self.name, allow_unicode=True)
        if is_new:
            self.remaining = self.total

        super().save(*args, **kwargs)

        if is_new:
            id_length = len(str(self.id))
            code_length = 6 - id_length
            zeros = "".join("0" for i in range(code_length))
            self.code = f"BOSE{zeros}{self.id}"
            self.save()

        action = f"added new inventory item with code - '{self.code}'"

        if not is_new:
            action = f"updated inventory item with code - '{self.code}'"

        add_user_activity(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted inventory - '{self.code}'"
        super().delete(*args, **kwargs)
        add_user_activity(created_by, action=action)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Shop(models.Model):
    created_by = models.ForeignKey(
        CustomUser, null=True, related_name="shops",
        on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(default="", editable=True,
                            max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_name = self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, allow_unicode=True)
        action = f"added new shop - '{self.name}'"
        if self.pk is not None:
            action = f"updated shp[] from - '{self.old_name}' to '{self.name}'"
        super().save(*args, **kwargs)
        add_user_activity(self.created_by, action=action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted shop - '{self.name}'"
        super().delete(*args, **kwargs)
        add_user_activity(created_by, action=action)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    created_by = models.ForeignKey(
        CustomUser, null=True, related_name="invoices",
        on_delete=models.SET_NULL
    )
    shop = models.ForeignKey(
        Shop, related_name="sale_shop", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted invoice - '{self.id}'"
        super().delete(*args, **kwargs)
        add_user_activity(created_by, action=action)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name="invoice_items", on_delete=models.CASCADE, null=True)  # remove null after migrations or sumin
    item = models.ForeignKey(
        Inventory, null=True, related_name="inventory_invoices",
        on_delete=models.SET_NULL
    )
    item_name = models.CharField(max_length=255, null=True)
    slug = models.SlugField(default="", editable=True,
                            max_length=255, blank=True)
    item_code = models.CharField(max_length=20, null=True)
    quantity = models.PositiveIntegerField()
    amount = models.FloatField(null=True)

    def save(self, *args, **kwargs):
        if self.item.remaining < self.quantity:
            raise Exception(
                f"item with code {self.item.code} does not have enough quantity")

        self.item_name = self.item.name
        self.item_code = self.item.code
        self.slug = slugify(self.item.name, allow_unicode=True)

        self.amount = self.quantity * self.item.price
        self.item.remaining = self.item.remaining - self.quantity
        self.item.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_code} - {self.quantity}"
