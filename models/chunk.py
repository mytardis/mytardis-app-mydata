from django.db import models


class Chunk(models.Model):
    """
    Chunk of a file uploaded by MyData app
    """

    chunk_id = models.CharField(max_length=36, unique=True, null=False)
    dfo_id = models.IntegerField(null=False)
    offset = models.BigIntegerField(null=False)
    created = models.DateTimeField(null=False)
    instrument_id = models.IntegerField(null=True)  # Might be uploaded manually
    user_id = models.IntegerField(null=False)

    class Meta:
        app_label = "mydata"
        ordering = ["offset"]
        unique_together = ["dfo_id", "offset"]

    def __str__(self):
        return str(self.dfo_id) + ":" + self.chunk_id
