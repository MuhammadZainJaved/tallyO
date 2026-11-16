from decimal import Decimal

from apps.catalog.models import Category, Product


def make_category(*, store, name="Groceries", slug="groceries", is_active=True):
    return Category.objects.create(store=store, name=name, slug=slug, is_active=is_active)


def make_product(
    *,
    store,
    name="Milk",
    slug="milk",
    category=None,
    price=Decimal("250.00"),
    is_active=True,
    track_inventory=False,
    stock_quantity=0,
):
    return Product.objects.create(
        store=store,
        category=category,
        name=name,
        slug=slug,
        price=price,
        is_active=is_active,
        track_inventory=track_inventory,
        stock_quantity=stock_quantity,
    )

