
from inventory_controller.models import Photo
from user_controller.models import CustomUser
from rest_framework.response import Response
from ecommerce_api.authentication import IsAuthenticatedCustom
from inventory_controller .serializers import(
    Inventory, InventoryGroup,
)
from .serializers import(
    InventoryGroupSerializer, InventorySerializer
)
from ecommerce_api.utils import CustomPagination
from rest_framework.viewsets import ModelViewSet
from ecommerce_api.utils import CustomPagination, get_query
from django.db.models import Q, Count, Sum, F
from django.db.models.functions import Coalesce, TruncMonth
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404


class CategoryView(ModelViewSet):
    queryset = InventoryGroup.objects.select_related(
        "belongs_to", "created_by").prefetch_related("inventories")
    serializer_class = InventoryGroupSerializer
    # permission_classes = (IsAuthenticatedCustom,)
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
                "created_by__fullname", "created_by__email", "name"
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results.annotate(
            total_items=Count('inventories')
        )
    all_sub_groups = []

    def _recursive(self, caty):
        # self.all_sub_groups.append(caty)
        sub_groups = self.queryset.filter(belongs_to=caty)
        for sub in sub_groups:
            self.all_sub_groups.append(sub)
        for sub in sub_groups:
            self._recursive(sub)

    def retrieve(self, request, *args, **kwargs):
        print("kwargs::", kwargs)
        slug = kwargs.get("slug", None)

        if not slug:
            return Response({"error": "no group/category with this slug found"}, status=400)
        caty = get_object_or_404(self.queryset, slug=slug)

        self.all_sub_groups = []
        sub_groups = self._recursive(caty)
        # print("sub_groups::", self.all_sub_groups)
        sub_groups_serializer = self.serializer_class(
            self.all_sub_groups, many=True, context={'request': request})
        # print("sub_groups_serializer::", sub_groups_serializer.data)
        serializer = self.serializer_class(caty, context={'request': request})
        return Response({"group": serializer.data, "groups": sub_groups_serializer.data})


class TopSellingProductCategory(APIView):
    queryset = Inventory.objects.select_related("group", "created_by")
    serializer_class = InventoryGroupSerializer
    # permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination

    def get(self, request):
        big_list = []
        qs = Inventory.objects.all()
        qs2 = InventoryGroup.objects.all()

        data = []
        all_categories = qs2.filter(belongs_to=None)
        big_list = []
        num = 7
        count = 0

        def recursive_(cat,  group_qs, inventory_qs):
            # print("\n")
            nonlocal count, num, big_list
            temp_list = []
            grouplist = group_qs.filter(belongs_to=cat)
            # print("initial::", cat)
            # print("grouplist::", grouplist)
            for group in grouplist:
                products = inventory_qs.filter(group=group)
                # print("products::", products[0:10])
                for item in products[:num]:
                    temp_list.append(item)
                    count += 1

                print("templist::", temp_list)

                for z in temp_list:
                    # check_existing =
                    # for zb in big_list:
                    if z not in big_list:
                        big_list.append(z)
                        count += 1

                # return big_list
                # print("biglist::", big_list)
                if count < num:
                    for p in temp_list:
                        p_group = p.group  # .belongs_to
                        # last= inventory_qs.filter(belongs_to=group)
                        # print("p.group:::", p_group)
                        recursive_(p_group,  group_qs, inventory_qs)
                else:
                    return big_list
            # print("biglist::", self.big_list)
            return big_list

        for cat in all_categories:

            count = 0
            big_list = []
            category_product = qs.filter(group=cat)
            items = category_product[0:num]
            temp_product = []
            for p in items:
                temp_product.append(p)

            if category_product.count() < num:
                count = category_product.count()

                res = recursive_(cat, qs2, qs)
                print(cat.name+" res::", res)
                print("\n")
                for b in res:
                    temp_product.append(b)

            serialized_items = InventorySerializer(temp_product, many=True,  context={
                'request': request}).data
            group = InventoryGroupSerializer(cat, context={
                                             'request': request}).data

            item = {"group": group, "items": serialized_items}
            data.append(item)
        sub_groups = []
        for sg in qs2:
            if sg.belongs_to is not None:
                sz = InventoryGroupSerializer(sg, context={
                    'request': request}).data
                sub_groups.append(sz)
        # print("subgroups:", sub_groups)

        data = {"data": data, "sub_groups": sub_groups}
        return Response(data, status=200)


class ProductView(ModelViewSet):
    queryset = Inventory.objects.select_related("group", "created_by")
    serializer_class = InventorySerializer
    # permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination
    lookup_field = "slug"

    def get_queryset(self):
        # import random
        # user = CustomUser.objects.get(email="admin@admin.com")
        # print("user:::", user)
        # _gl = ["Kitchen", "Pool", "Bathroom", "Playground"]
        # _inames = ["capy", "lapy", "grizzle", "lane", "ayo", "lero",
        #            "fronty", "backy", "soary", "undry", "bizzy", "giggy", "giggy-gig"]
        # new_inames = []
        # for c in _inames:
        #     for e in range(2):
        #         new_inames.append(c+str(random.randrange(1, 1000)))

        # for g in _gl:
        #     try:
        #         inve_g = InventoryGroup.objects.create(name=g, created_by=user)
        #     except Exception as e:
        #         print("here111:::", e)
        # for v in new_inames:
        #     try:

        #         get_gr = InventoryGroup.objects.get(name=_gl[random.randrange(1, len(
        #             _gl)-1)])
        #         _inv_item = Inventory.objects.create(name=v, group=get_gr, total=random.randrange(
        #             1, 1000), price=random.randrange(1, 2000), code=random.randrange(1, 1000), description="Cool product")
        #         photo = Photo.objects.all()[0]
        #         _inv_item.photo.add(photo)
        #         _inv_item.save()
        #     except Exception as e:
        #         print("here2222:::", e)

        data = self.request.query_params.dict()
        print("params:::", data)
        data.pop("page", None)
        keyword = data.pop("keyword", None)
        mode = data.pop("mode", None)
        results = self.queryset.filter(**data)
        temp_results = []

        def _recursive(product):
            # nonlocal temp_results
            products = self.queryset.filter(Q(group__belongs_to=product.group))
            # results = results | products
            for p in products:
                exists_count = temp_results.count(p)
                if exists_count > 0:
                    pass
                else:
                    temp_results.append(p)
            for p2 in products:
                _recursive(p2)
        if keyword:
            if mode:
                search_fields = (
                    "name",
                )
                query = get_query(keyword, search_fields)
                results = results.filter(query)

            else:
                search_fields = (
                    "group__slug",
                    "group__belongs_to__slug"
                )
                query = get_query(keyword, search_fields)
                print("query::", query)
                results = results.filter(query)
                print("results::", results)

                for product in results:
                    exists_count = temp_results.count(product)
                    if exists_count > 0:
                        pass
                    else:
                        temp_results.append(product)
                for product in results:
                    _recursive(product)

                return temp_results

        return results


class RelatedProductView(ModelViewSet):
    queryset = Inventory.objects.select_related("group", "created_by")
    serializer_class = InventorySerializer
    # permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination
    lookup_field = "slug"

    def get_queryset(self):
        # if self.request.method.lower() != "get":
        #     return self.queryset

        data = self.request.query_params.dict()
        print("params:::", data)
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            # if  keyword=="":

            search_fields = (

                "name",  # , "group__name", "group__belongs_to__name"
            )
            query = get_query(keyword, search_fields)
            print("query::", query)
            print("kk:", keyword)
            return results.filter(query).exclude(Q(name=keyword))

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)
