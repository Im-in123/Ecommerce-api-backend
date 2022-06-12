
from rest_framework.viewsets import ModelViewSet
from .serializers import (
    Inventory, InventorySerializer, InventoryGroupSerializer, InventoryGroup,
    Shop, ShopSerializer, Invoice, InvoiceSerializer, InventoryWithSumSerializer,
    ShopWithAmountSerializer, InvoiceItem, Photo, Size, Color
)
from rest_framework.response import Response
from ecommerce_api.authentication import IsAuthenticatedCustom
from ecommerce_api.utils import CustomPagination, get_query
from django.db.models import Count, Sum, F
from django.db.models.functions import Coalesce, TruncMonth
from user_controller.views import add_user_activity
from user_controller.models import CustomUser
import csv
import codecs
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import os
from django.conf import settings
from pyuploadcare import Uploadcare
uploadcare = Uploadcare(
    public_key=settings.UPLOADCARE['pub_key'], secret_key=settings.UPLOADCARE['secret'])


class InventoryView(ModelViewSet):
    queryset = Inventory.objects.select_related("group", "created_by")
    serializer_class = InventorySerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                "code",
                "group__name", "name"
            )
            query = get_query(keyword, search_fields)
            return results.filter(query)

        return results

    def create(self, request, *args, **kwargs):

        try:
            request.data._mutable = True
        except:
            pass
        request.data.update({"created_by_id": request.user.id})

        img_ids = request.data.pop("img_ids", None)
        sizes = request.data.pop("sizes", None)
        colors = request.data.pop("colors", None)

        print("ids:::", img_ids)
        print("sizes:::", sizes)
        print("colors:::", colors)

        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        print(serializer.data)
        inv = get_object_or_404(self.queryset, id=serializer.data.get("id"))
        if sizes and len(sizes) <= 10:

            for name in sizes:
                name = name.strip()
                if name != "" or name != "#":

                    try:

                        ts = Size.objects.get(name=name)
                    except:
                        ts = Size.objects.create(name=name)
                        ts = Size.objects.get(id=ts.id)
                    inv.sizes.add(ts)

        if colors and len(colors) <= 10:

            for name in colors:
                name = name.strip()
                if name != "" or name != "#":

                    try:

                        ts = Color.objects.get(name=name)
                    except:
                        ts = Color.objects.create(name=name)
                        ts = Color.objects.get(id=ts.id)
                    inv.colors.add(ts)

        if img_ids:
            try:
                for i in img_ids:
                    try:
                        try:
                            item = Photo.objects.get(id=int(i))
                        except Exception as e:
                            print(e)
                            item = None
                        if item:
                            if os.path.isfile(item.image.path):
                                ucare_file = None
                                with open(item.image.path, 'rb') as file_object:
                                    ucare_file = uploadcare.upload(file_object)
                                print("ucare_file::", ucare_file)

                                item.photo = ucare_file
                                inv.photo.add(item)
                                item.has_inv = True
                                inv.save()
                                item.save()
                    except Exception as e:
                        print(e)
                        try:
                            item.has_inv = False
                            item.save()
                            file_delete = uploadcare.file(item.photo.cdn_url)
                            print("file_delete::", file_delete)
                            file_delete.delete()
                            if file_delete.is_removed:
                                item.delete()
                        except Exception as e:
                            print(e)
                old_p = Photo.objects.all().filter(created_by=request.user, has_inv=False)
                for p in old_p:
                    p.delete()
                return Response({"success": "success"}, status=200)

            except Exception as e:
                print(e)
                inv.delete()
                return Response({"error": "error"}, status=400)
        inv.delete()
        return Response({"error": "error"}, status=400)

    def patch(self, request):
        try:
            request.data._mutable = True
        except:
            pass
        img_ids = request.data.pop("img_ids", None)
        sizes = request.data.pop("sizes", None)
        colors = request.data.pop("colors", None)

        print("ids:::", img_ids)
        print("sizes:::", sizes)
        print("colors:::", colors)

        id = request.data.get("id", None)
        inv = get_object_or_404(self.queryset, id=id)
        if sizes:
            pass
        else:
            for i in inv.sizes.all():
                inv.sizes.remove(i)
        if sizes and len(sizes) <= 10:
            for i in inv.sizes.all():
                inv.sizes.remove(i)
            for name in sizes:
                name = name.strip()
                if name != "" or name != "#":

                    try:

                        ts = Size.objects.get(name=name)
                    except:
                        ts = Size.objects.create(name=name)
                        ts = Size.objects.get(id=ts.id)
                    inv.sizes.add(ts)
            inv.save()

        if colors:
            pass
        else:
            for i in inv.colors.all():
                inv.colors.remove(i)

        if colors and len(colors) <= 10:
            for i in inv.colors.all():
                inv.colors.remove(i)
            for name in colors:
                name = name.strip()
                if name != "" or name != "#":

                    try:
                        ts = Color.objects.get(name=name)
                    except:
                        ts = Color.objects.create(name=name)
                        ts = Color.objects.get(id=ts.id)
                    inv.colors.add(ts)

        if img_ids:
            try:
                for i in img_ids:
                    try:
                        try:
                            item = Photo.objects.get(id=int(i))
                        except Exception as e:
                            print(e)
                            item = None
                        if item:
                            if os.path.isfile(item.image.path):
                                try:
                                    ucare_file = None
                                    print("edhhh:")
                                    with open(item.image.path, 'rb') as file_object:
                                        ucare_file = uploadcare.upload(
                                            file_object)
                                    print("ucare_file::", ucare_file)

                                    item.photo = ucare_file
                                    inv.photo.add(item)
                                    item.has_inv = True
                                    inv.save()
                                    item.save()
                                    # comment out try block for heroku
                                except Exception as e:
                                    print(e)
                                    # comment out for heroku
                                    inv.photo.add(item)
                                    item.has_inv = True
                                    item.save()

                    except Exception as e:
                        print(e)
                        try:
                            print("edhhh:", item)

                            item.has_inv = False
                            item.save()
                            file_delete = uploadcare.file(item.photo.cdn_url)
                            print("file_delete::", file_delete)
                            file_delete.delete()
                            if file_delete.is_removed:
                                item.delete()
                        except Exception as e:
                            print(e)
                old_p = Photo.objects.all().filter(created_by=request.user, has_inv=False)
                for p in old_p:
                    p.delete()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(
            inv, data=request.data, partial=True,  context={
                'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class InventoryGroupView(ModelViewSet):
    queryset = InventoryGroup.objects.select_related(
        "belongs_to", "created_by").prefetch_related("inventories")
    serializer_class = InventoryGroupSerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                "created_by__email", "name"
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results.annotate(
            total_items=Count('inventories')
        )

    def create(self, request, *args, **kwargs):
        print("in create")
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)

    def patch(self, request):
        try:
            request.data._mutable = True
        except:
            pass
        id = request.data.get("id", None)
        belongs_to_id = request.data.get("belongs_to_id", None)
        if str(id) == str(belongs_to_id):
            return Response({"error": {"belongs_to:": ["invalid belongs_to"]}}, status=400)
        group = get_object_or_404(self.queryset, id=id)

        serializer = self.serializer_class(
            group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class ShopView(ModelViewSet):
    queryset = Shop.objects.select_related("created_by")
    serializer_class = ShopSerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                "created_by__email", "name"
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)

    def patch(self, request):
        try:
            request.data._mutable = True
        except:
            pass
        id = request.data.get("id", None)
        shop = get_object_or_404(self.queryset, id=id)

        serializer = self.serializer_class(
            shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class InvoiceView(ModelViewSet):
    queryset = Invoice.objects.select_related(
        "created_by", "shop").prefetch_related("invoice_items")
    serializer_class = InvoiceSerializer
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                "created_by__email", "shop__name"
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)


class SummaryView(ModelViewSet):
    http_method_names = ('get',)
    permission_classes = (IsAuthenticatedCustom,)
    queryset = InventoryView.queryset

    def list(self, request, *args, **kwargs):
        total_inventory = InventoryView.queryset.filter(
            remaining__gt=0
        ).count()
        total_group = InventoryGroupView.queryset.count()
        total_shop = ShopView.queryset.count()
        total_users = CustomUser.objects.filter(is_superuser=False).count()

        return Response({
            "total_inventory": total_inventory,
            "total_group": total_group,
            "total_shop": total_shop,
            "total_users": total_users
        })


class SalePerformanceView(ModelViewSet):
    http_method_names = ('get',)
    permission_classes = (IsAuthenticatedCustom,)
    queryset = InventoryView.queryset

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get('total', None)
        query = self.queryset

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(
                    inventory_invoices__created_at__range=[
                        start_date, end_date]
                )

        items = query.annotate(
            sum_of_item=Coalesce(
                Sum("inventory_invoices__quantity"), 0
            )
        ).order_by('-sum_of_item')[0:10]

        response_data = InventoryWithSumSerializer(items, many=True).data
        return Response(response_data)


class SaleByShopView(ModelViewSet):
    http_method_names = ('get',)
    permission_classes = (IsAuthenticatedCustom,)
    queryset = InventoryView.queryset

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get('total', None)
        monthly = query_data.get('monthly', None)
        query = ShopView.queryset

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(
                    sale_shop__created_at__range=[start_date, end_date]
                )

        if monthly:
            shops = query.annotate(month=TruncMonth('created_at')).values(
                'month', 'name').annotate(amount_total=Sum(
                    F("sale_shop__invoice_items__quantity") *
                    F("sale_shop__invoice_items__amount")
                ))

        else:
            shops = query.annotate(amount_total=Sum(
                F("sale_shop__invoice_items__quantity") *
                F("sale_shop__invoice_items__amount")
            )).order_by("-amount_total")

        response_data = ShopWithAmountSerializer(shops, many=True).data
        return Response(response_data)


class PurchaseView(ModelViewSet):
    http_method_names = ('get',)
    permission_classes = (IsAuthenticatedCustom,)
    queryset = InvoiceView.queryset

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get('total', None)
        query = InvoiceItem.objects.select_related("invoice", "item")

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(
                    created_at__range=[start_date, end_date]
                )

        query = query.aggregate(
            amount_total=Sum(F('amount') * F('quantity')), total=Sum('quantity')
        )

        return Response({
            "price": "0.00" if not query.get("amount_total") else query.get("amount_total"),
            "count": 0 if not query.get("total") else query.get("total"),
        })


class InventoryCSVLoaderView(ModelViewSet):
    http_method_names = ('post',)
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = InventorySerializer

    def create(self, request, *args, **kwargs):
        try:
            data = request.FILES['data']
        except Exception as e:
            raise Exception("You need to provide inventory CSV 'data'")

        inventory_items = []

        try:
            csv_reader = csv.reader(codecs.iterdecode(data, 'utf-8'))
            for row in csv_reader:
                if not row[0]:
                    continue
                inventory_items.append(
                    {
                        "group_id": row[0],
                        "total": row[1],
                        "name": row[2],
                        "price": row[3],
                        "photo": row[4],
                        "created_by_id": request.user.id
                    }
                )
        except csv.Error as e:
            raise Exception(e)

        if not inventory_items:
            raise Exception("CSV file cannot be empty")

        data_validation = self.serializer_class(
            data=inventory_items, many=True)
        data_validation.is_valid(raise_exception=True)
        data_validation.save()

        return Response({"success": "Inventory items added successfully"})


class AllAvailableGroups(APIView):
    queryset = Inventory.objects.select_related("group", "created_by")
    serializer_class = InventoryGroupSerializer
    permission_classes = (IsAuthenticatedCustom,)

    def get(self, request):

        qs = InventoryGroup.objects.all()
        qs = self.serializer_class(qs, many=True, context={
                                   'request': request}).data
        return Response({"data": qs})


class PhotoHandler(APIView):
    serializer_class = InventoryGroupSerializer
    permission_classes = (IsAuthenticatedCustom,)
    queryset = Inventory.objects.all()

    def post(self, request):
        print("reuest::", request.data)
        image = request.data.get("image", None)
        inv_id = request.data.get("inv_id", None)
        photo_id = request.data.get("photo_id", None)
        if image:
            p = Photo.objects.create(image=image, created_by=request.user)
            return Response({"data": p.id})

        if inv_id and photo_id:
            inv = get_object_or_404(self.queryset, id=inv_id)
            photo = get_object_or_404(Photo.objects.all(), id=photo_id)
            if photo in inv.photo.all():
                if photo.photo:
                    try:

                        print("cdn::", photo.photo.cdn_url)

                        file_delete = uploadcare.file(photo.photo.cdn_url)
                        print("file_delete::", file_delete)
                        file_delete.delete()
                        if file_delete.is_removed:
                            photo.has_inv = False
                            photo.save()
                            photo.delete()
                            return Response({"data": "success"}, status=200)

                    except Exception as e:
                        print(e)
                        return Response({"error": "error"}, status=400)

                inv.photo.remove(photo)
                photo.delete()
                return Response({"data": "success"}, status=200)
