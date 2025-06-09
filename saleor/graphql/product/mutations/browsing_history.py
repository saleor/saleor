import graphene
from graphql.error import GraphQLError
from saleor.product.models import Product, ProductBrowsingHistory as ProductBrowsingHistoryModel
from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.utils import from_global_id_or_error
from saleor.graphql.core.types import ProductError
from ..types.browsing_history import ProductBrowsingHistory


class RecordProductView(BaseMutation):
    """Record product browsing"""
    browsing_history = graphene.Field(ProductBrowsingHistory)
    
    class Arguments:
        product_id = graphene.ID(required=True, description="product ID")
    
    class Meta:
        description = "Record the user's browsing behavior"
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def perform_mutation(cls, _root, info, product_id):
        # Get the product
        try:
            product_pk = from_global_id_or_error(product_id, 'Product')[1]
            product = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist:
            raise GraphQLError("Product does not exist")
        
        # Get user and session information
        user = info.context.user if info.context.user.is_authenticated else None
        session_key = info.context.session.session_key
        ip_address = cls.get_client_ip(info.context)
        
        # Record browsing history
        history_entry = ProductBrowsingHistoryModel.record_view(
            product=product,
            user=user,
            session_key=session_key,
            ip_address=ip_address
        )
        
        return RecordProductView(browsing_history=history_entry)
    
    @staticmethod
    def get_client_ip(request):
        """Get the client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ClearBrowsingHistory(BaseMutation):
    """Clear browsing history"""
    success = graphene.Boolean()
    
    class Meta:
        description = "Clear all browsing history of the current user"
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def perform_mutation(cls, _root, info):
        user = info.context.user
        
        if user.is_authenticated:
            # Clear logged in user history
            deleted_count = ProductBrowsingHistoryModel.objects.filter(
                user=user
            ).delete()[0]
        else:
            # Clear anonymous user history
            session_key = info.context.session.session_key
            if session_key:
                deleted_count = ProductBrowsingHistoryModel.objects.filter(
                    session_key=session_key,
                    user=None
                ).delete()[0]
            else:
                deleted_count = 0
        
        return ClearBrowsingHistory(success=deleted_count > 0)

class RemoveBrowsingHistoryItem(BaseMutation):
    """Remove browsing history for specific products"""
    success = graphene.Boolean()
    
    class Arguments:
        product_id = graphene.ID(required=True, description="Items to remove ID")
    
    class Meta:
        description = "Remove browsing history for specific products"
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def perform_mutation(cls, _root, info, product_id):
        user = info.context.user
        
        try:
            product_pk = from_global_id_or_error(product_id, 'Product')[1]
        except Exception:
            raise GraphQLError("Invalid product ID")
        
        if user.is_authenticated:
            # Remove specific records of logged in users
            deleted_count = ProductBrowsingHistoryModel.objects.filter(
                user=user,
                product_id=product_pk
            ).delete()[0]
        else:
            # Remove specific records for anonymous users
            session_key = info.context.session.session_key
            if session_key:
                deleted_count = ProductBrowsingHistoryModel.objects.filter(
                    session_key=session_key,
                    user=None,
                    product_id=product_pk
                ).delete()[0]
            else:
                deleted_count = 0
        
        return RemoveBrowsingHistoryItem(success=deleted_count > 0)