import uuid

from django.db import models
from django.utils.html import format_html


class TimeStamped(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Author(models.Model):
    name = models.CharField("full name", max_length=100)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.name

    def initials(self):
        return "".join(part[0] for part in self.name.split())

    def book_count(self):
        return self.books.count()

    def bold_name(self):
        return format_html("<b>{}</b>", self.name)

    @property
    def shout(self):
        return self.name.upper()


class Book(models.Model):
    STATUS_CHOICES = [
        ("Available", [("pub", "Published"), ("oop", "Out of print")]),
        ("draft", "Draft"),
    ]

    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="books", null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    pages = models.PositiveIntegerField(default=0)
    cover = models.FileField(upload_to="covers/", blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.title


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Publisher(TimeStamped):
    code = models.SlugField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Novel(Book):
    """Multi-table inheritance: the pk is a OneToOneField to Book."""

    genre = models.CharField(max_length=50, blank=True)
