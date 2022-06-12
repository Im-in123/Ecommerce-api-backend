from django.urls import path, include
from .views import (
    CategoryView,
    ProductView,
    RelatedProductView,
    TopSellingProductCategory,
    RelatedProductView
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=True)

router.register('category', CategoryView, "category"),
router.register('product', ProductView, "product")
router.register('related-product', RelatedProductView, "related-product")

# router.register('top-product-categories',
#                 TopSellingProductCategory, "top-product-categories")

# router.register('inventory-csv', InventoryCSVLoaderView, "inventory-csv")
# router.register('shop', ShopView, "shop")
# router.register('summary', SummaryView, "summary")
# router.register('purchase-summary', PurchaseView, "purchase-summary")
# router.register('sales-by-shop', SaleByShopView, "sales-by-shop")
# router.register('group', InventoryGroupView, "group")
# router.register('top-selling', SalePerformanceView, "top-selling")
# router.register('invoice', InvoiceView, "invoice")

urlpatterns = [
    path("", include(router.urls)),
    path("top-product-categories", TopSellingProductCategory.as_view())
]
