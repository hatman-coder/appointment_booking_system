from django.db import models

class Division(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    class Meta:
        db_table = 'divisions'
        ordering = ['name']

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='districts')
    
    class Meta:
        db_table = 'districts'
        ordering = ['name']
        unique_together = ['name', 'division']

    def __str__(self):
        return f"{self.name}, {self.division.name}"

class Thana(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='thanas')
    
    class Meta:
        db_table = 'thanas'
        ordering = ['name']
        unique_together = ['name', 'district']

    def __str__(self):
        return f"{self.name}, {self.district.name}"