from django.db import models


class Product(models.Model):
    product_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    current_stock = models.IntegerField(default=0)

    def __str__(self):
        return self.product_id


class SalesData(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    date = models.DateField()
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=20)

    daily_sales = models.IntegerField()
    stock_level = models.IntegerField()

    season = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.product.product_id} - {self.size} - {self.date}"