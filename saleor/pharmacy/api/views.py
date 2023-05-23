from rest_framework import generics
from django.views import generic
from django.http import HttpResponse
from django.template import loader

from ..pharmacy.models import Patient
from .serializers import HealthProfileSerializer


class HealthProfilesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = HealthProfileSerializer
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
