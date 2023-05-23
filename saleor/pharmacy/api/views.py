from rest_framework import generics
from django.views import generic
from django.http import HttpResponse
from django.template import loader

from ..models import Patient
from .serializers import HealthProfileSerializer


class HealthProfileList(generics.ListCreateAPIView):
    serializer_class = HealthProfileSerializer

    def get_queryset(self):
        customer_uuid = self.kwargs["uuid"]
        queryset = Patient.objects.for_customer_uuid(customer_uuid)
        if isinstance(queryset, list):
            return queryset
        else:
            items = [queryset]
            return items

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
