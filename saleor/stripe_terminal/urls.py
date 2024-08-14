from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CheckoutViewSet, OrderCreateFromCheckoutViewSet, OrderViewSet, FetchVariantsView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'checkouts', CheckoutViewSet, basename='checkout')
router.register(r'orders', OrderCreateFromCheckoutViewSet, basename='order_create_from_checkout')
router.register(r'order_management', OrderViewSet, basename='order')

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include(router.urls)),
    path('fetch_variants/', FetchVariantsView.as_view(), name='fetch_variants'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]


