from django.db import models
class Product(models.Model):
    id=models.CharField(max_length=100)
    excerpt=models.TextField()
    def _str_(self):
            
        return self.title