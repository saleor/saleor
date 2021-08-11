from saleor.saleor.custom import models
from saleor.saleor.graphql.utils import get_user_or_app_from_context


# def resolve_custom_by_id(info, id):
#     requestor = get_user_or_app_from_context(info.context)
#     visible_customs = models.Custom.objects.visible_to_user(requestor).values_list(
#         "pk", flat=True
#     )
#     return (
#         models.visible_customs.objects.filter(product__id__in=visible_products)
#         .filter(id=id)
#         .first()
#     )
