from django.db import models

class JobCategoryManager(models.Manager):
    def validate(self, category):
        validation_errors = []
        if self.filter(category__iexact=category).exists():    
            validation_errors.append(f"Category [{category}] already exists")
        if len(category) < 2:
            validation_errors.append(f"Category must be at least 2 chars")
        return validation_errors

class JobCategory(models.Model):
    category = models.CharField(max_length=100)
    objects = JobCategoryManager()

class UserManager(models.Manager):
    def validate(self, first_name, last_name, email):
        validation_errors = []
        if self.filter(email__iexact=email).exists():    
            validation_errors.append(f"There was already a user with email [{email}]! Registration denied!")
        return validation_errors

class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    user_level = models.CharField(max_length=100, default="normal")
    description = models.TextField(default="put description here")
    password_hash = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()

class JobManager(models.Manager):
    def validate(self, title, description, location):
        validation_errors = []
        if len(title) < 3:   
            validation_errors.append(f"Title must be at least 3 chars")
        if len(description) < 10:
            validation_errors.append(f"Description must be at least 10 chars")
        if location == "":
            validation_errors.append(f"Location cannot be blank")
        return validation_errors

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    categories = models.ManyToManyField(JobCategory, related_name="jobs")
    users = models.ManyToManyField(User, related_name="jobs")
    created_by = models.ForeignKey(User, related_name="created_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    objects = JobManager()    