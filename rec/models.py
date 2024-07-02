from django.db import models


class Facerec(models.Model):
    id_person = models.CharField(max_length=100)
    event = models.CharField(max_length=100)
    time = models.DateTimeField(null=True)

class Id_persons(models.Model):
    id_person = models.CharField(primary_key=True)
    person = models.CharField(max_length=100)

    def __str__(self):
        return self.person