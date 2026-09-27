from django.db import transaction

from apps.inventory.models import InventoryCategory, ProductInventoryProfile, ReorderRule, StockMovement


@transaction.atomic
def clear_inventory_data(*, actor):
    profiles = list(ProductInventoryProfile.objects.select_related('product'))
    archive_ids = [profile.product_id for profile in profiles if profile.created_through_inventory]
    counts = {
        'movements': StockMovement.objects.count(),
        'reorder_rules': ReorderRule.objects.count(),
        'profiles': len(profiles),
        'categories': InventoryCategory.objects.count(),
        'products_archived': len(archive_ids),
    }
    StockMovement.objects.all().delete()
    ReorderRule.objects.all().delete()
    ProductInventoryProfile.objects.all().delete()
    InventoryCategory.objects.all().delete()
    if archive_ids:
        from apps.products.models import Product
        Product.objects.filter(id__in=archive_ids).update(is_active=False)
    return counts
