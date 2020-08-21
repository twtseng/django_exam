from django.shortcuts import render, HttpResponse, redirect, reverse
from django.http import JsonResponse
from django.db.models import Max, Count
import bcrypt
import sys
from . import models

# Create your views here.
def get_logged_in_user(request):
    if "user_email" in request.session and "password_hash" in request.session:
        email = request.session["user_email"]
        password_hash = request.session["password_hash"]
        try:
            user = models.User.objects.get(email__iexact=email, password_hash__iexact=password_hash)
            request.session["logged_in_user"] = f"{user.first_name} {user.last_name}"
            return user
        except models.User.DoesNotExist:
            return None
    return None

def signin_view(request):
    print("in signin_view")
    logged_in_user = get_logged_in_user(request)
    if logged_in_user == None:
        return render(request,'login_view.html')
    else:
        return redirect(reverse('dashboard_view'))

def register_user_api(request):
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        password = request.POST["password"]
        validation_errors = models.User.objects.validate(first_name, last_name, email)
        if len(validation_errors)>0:  
            response["status"] = "failed"
            error_string = ""
            for e in validation_errors:
                error_string += e
            response["message"] = error_string
        else:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            models.User.objects.create(first_name=first_name, last_name=last_name, email=email, password_hash=password_hash)
            response["status"] = "succeeded"
            response["message"] = f"User with email [{email}] added successfully."
    return JsonResponse(response)

def login_user_api(request):
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            user = models.User.objects.get(email__iexact=email)
            response["status"] = "succeeded"
            response["message"] = f"User with email [{email}] found."
            if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                response["status"] = "succeeded"
                response["message"] = f"User with email [{email}] found. And password was correct"
                
                request.session["user_email"] = email
                request.session["password_hash"] = user.password_hash
                request.session.save()
            else:
                response["status"] = "failed"
                response["message"] = f"User with email [{email}] found. But password was incorrect"
        except models.User.DoesNotExist:
            response["status"] = "failed"
            response["message"] = f"User with email [{email}] not found."
    return JsonResponse(response)

def logout_user_api(request):
    request.session.clear()
    return redirect(reverse('signin_view'))

def user_level_control(value,is_admin,user_id):
    if is_admin:
        if value == "admin":
            return f"<select id='user_level' class='user_level_dropdown' user_id='{user_id}'><option value='admin' selected>admin</option><option value='normal'>normal</option></select>"
        else:
            return f"<select id='user_level' class='user_level_dropdown' user_id='{user_id}'><option class='user_level_dropdown' value='admin'>admin</option><option value='normal' selected>normal</option></select>"
    else:
        return value

def manage_users_view(request):
    logged_in_user = get_logged_in_user(request)
    data_columns=["id","name","email","created_at","user_level"]
    if logged_in_user.user_level == "admin":
        data_columns.append("admin")
    data_rows = []
    for user in models.User.objects.all():
        data_row = [
            user.id,
            f"<a href='../users/edit/{user.id}'>{user.first_name} {user.last_name}</a>",
            user.email,
            user.created_at.strftime('%m-%d-%Y'),
            user_level_control(user.user_level, logged_in_user.user_level == "admin", user.id)
        ]
        if logged_in_user.user_level == "admin":
            data_row.append(f'<a href="../users/edit/{user.id}">edit</a> | <a href="/users/delete/{user.id}">remove</a>')
        data_rows.append(data_row)

    context = {
        'data_columns' : data_columns,
        'data_rows' : data_rows,
        'user_level' : logged_in_user.user_level,
    }
    
    if "logged_in_user" in request.session:
        return render(request,"manage_users.html", context)
    else:
        return redirect(reverse('signin_view'))

def new_user(request):
    logged_in_user = get_logged_in_user(request)
    if logged_in_user.user_level == "admin":
        return render(request,"new_user.html")
    else:
        return redirect(reverse('signin_view'))

def delete_user(request, user_id):
    logged_in_user = get_logged_in_user(request)
    if logged_in_user.user_level == "admin":
        user = models.User.objects.get(id=int(user_id))
        user.delete()
        return redirect(reverse('manage_users_view'))
    else:
        return redirect(reverse('signin_view'))    

def edit_user_view(request, user_id):
    if "logged_in_user" not in request.session:
        return redirect(reverse('signin_view'))
    logged_in_user = get_logged_in_user(request)
    user = models.User.objects.get(id=int(user_id))
    user_level_control_html = user_level_control(user.user_level, logged_in_user.user_level == "admin", user.id)
    context = {
        'user' : user,
        'user_level_control_html' : user_level_control_html,
    }
    return render(request,"edit_user.html", context)

def set_user_level_api(request):
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        user_id = int(request.POST["user_id"])
        user_level = request.POST["user_level"]
        try:
            user = models.User.objects.get(id=user_id)
            user.user_level = user_level
            user.save()
            response["status"] = "succeeded"
            response["message"] = f"[{user.email}] set to user_level [{user.user_level}]."
        except:
            response['status'] = "failed"
            response['message'] = str(sys.exc_info()[0])
    return JsonResponse(response)

def edit_profile_api(request):
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        try:
            user_id = int(request.POST["user_id"])
            user = models.User.objects.get(id=user_id)
            user.first_name = request.POST["first_name"]
            user.last_name = request.POST["last_name"]
            user.email = request.POST["email"]
            if request.POST["user_level"] > "":
                user.user_level = request.POST["user_level"]
            user.save()
            response["status"] = "succeeded"
            response["message"] = f"[{user.email}] updated with new profile info."
        except:
            response['status'] = "failed"
            response['message'] = str(sys.exc_info()[0])
    return JsonResponse(response)

def update_password_api(request):
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        try:
            user_id = int(request.POST["user_id"])
            user = models.User.objects.get(id=user_id)
            password = request.POST["password"]
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user.password_hash = password_hash
            user.save()
            response["status"] = "succeeded"
            response["message"] = f"Password updated for [{user.email}]."
        except:
            response['status'] = "failed"
            response['message'] = str(sys.exc_info()[0])
    return JsonResponse(response)    

def new_job_view(request):
    if "logged_in_user" not in request.session:
        return redirect(reverse('signin_view'))
    logged_in_user = get_logged_in_user(request)
    job_categories = models.JobCategory.objects.all()
    context = {
        'logged_in_user' : logged_in_user,
        'job_categories' : job_categories,
    }
    return render(request,"new_job.html", context)

def add_job_api(request):
    user = get_logged_in_user(request)
    print(f"in add_job_api, user {user}")
    print(request)
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        print(f"in add_job_api POST block")
        try:
            # Add add_category (if needed)
            add_category = request.POST["add_category"]
            if add_category > " ":
                if not models.JobCategory.objects.filter(category__iexact=add_category).exists():
                    models.JobCategory.objects.create(category=add_category)
                print(f"Added new category: {add_category}")

            job_title = request.POST["job_title"]
            job_description = request.POST["job_description"]
            job_location = request.POST["job_location"]
            validation_errors = models.Job.objects.validate(job_title, job_description, job_location)
            print(f"validation_errors: {validation_errors}")
            if len(validation_errors)>0:
                error_string = ",".join(validation_errors)
                response['status'] = "failed"
                response['message'] = error_string
            else:
                job = models.Job.objects.create(
                    title=job_title,
                    description=job_description,
                    location=job_location,
                    created_by=user
                )
                job_categories_string = request.POST["job_categories_string"]
                if (job_categories_string > " "):
                    job_categories = job_categories_string.split(",")
                    for cat in models.JobCategory.objects.all():
                        if cat.category in job_categories or cat.category==add_category:
                            print(f"Adding category [{cat.category}]")
                            job.categories.add(cat)
                        job.save()
                response["status"] = "succeeded"
                response["message"] = f"Created Job with Title=[{job_title}]."
        except:
            response['status'] = "failed"
            response['message'] = str(sys.exc_info()[0])
    return JsonResponse(response)

def dashboard_view(request):
    if "logged_in_user" in request.session:
        logged_in_user = get_logged_in_user(request)
        all_jobs = models.Job.objects.all()
        everyones_jobs_data_columns=["Job","Location","Created by me","Actions"]
        everyones_jobs_data_rows = []
        my_jobs_data_columns=["Job","Actions"]
        my_jobs_data_rows = []
        for job in all_jobs:
            created_by_me = job.created_by == logged_in_user
            in_my_jobs = job in logged_in_user.jobs.all()
            actions=f"<a href='../jobs/{job.id}'>View</a>"
            if created_by_me:
                actions += f" | <a href='../jobs/remove/{job.id}'>Remove</a>"
                actions += f" | <a href='../jobs/edit/{job.id}'>Edit</a>"
            actions += f" | <a href='../jobs/add_job_to_user/{job.id}'>Add job to me</a>"
            
            data_row = [
                job.title,
                job.location,
                created_by_me,
                actions,
            ]
            if not in_my_jobs:
                everyones_jobs_data_rows.append(data_row)
            else:
                myactions=f"<a href='../jobs/{job.id}'>View</a>"
                myactions += f" | <a href='../jobs/remove/{job.id}'>Done</a>"
                myactions += f" | <a href='../jobs/remove_job_from_user/{job.id}'>Give up</a>"
                my_jobs_data_rows.append([job.title, myactions])

        context = {
            'everyones_jobs_data_columns' : everyones_jobs_data_columns,
            'everyones_jobs_data_rows' : everyones_jobs_data_rows,
            'my_jobs_data_columns' : my_jobs_data_columns,
            'my_jobs_data_rows' : my_jobs_data_rows
        }
        return render(request,"dashboard.html", context)
    else:
        return redirect(reverse('signin_view'))

def view_job_view(request, job_id):
    if "logged_in_user" not in request.session:
        return redirect(reverse('signin_view'))
    logged_in_user = get_logged_in_user(request)
    job = models.Job.objects.get(id=job_id)
    created_by_me = job.created_by == logged_in_user
    in_my_jobs = job in logged_in_user.jobs.all()
    context = {
        'job_id' : job.id,
        'title' : job.title,
        'description' : job.description,
        'location' : job.location,
        'categories' : job.categories.all(),
        'in_my_jobs' : in_my_jobs,
        'created_by_me' : created_by_me,
    }
    return render(request,"view_job.html", context)

def remove_job(request, job_id):
    if "logged_in_user" in request.session:
        job = models.Job.objects.get(id = job_id)
        job.delete()
    return redirect(reverse('dashboard_view'))

def add_job_to_user(request, job_id):
    if "logged_in_user" in request.session:
        logged_in_user = get_logged_in_user(request)
        job = models.Job.objects.get(id = job_id)
        if job not in logged_in_user.jobs.all():
            logged_in_user.jobs.add(job)
    return redirect(reverse('dashboard_view'))

def remove_job_from_user(request, job_id):
    if "logged_in_user" in request.session:
        logged_in_user = get_logged_in_user(request)
        job = models.Job.objects.get(id = job_id)
        if job in logged_in_user.jobs.all():
            logged_in_user.jobs.remove(job)
    return redirect(reverse('dashboard_view'))

def edit_job_view(request, job_id):
    if "logged_in_user" not in request.session:
        return redirect(reverse('signin_view'))
    logged_in_user = get_logged_in_user(request)
    job = models.Job.objects.get(id=job_id)
    created_by_me = job.created_by == logged_in_user
    in_my_jobs = job in logged_in_user.jobs.all()

    categories = []
    for cat in models.JobCategory.objects.all():
        is_selected = cat in job.categories.all()
        categories.append(
            {
                'category' : cat.category,
                'is_selected' : is_selected
            }
        )

    context = {
        'job_id' : job.id,
        'title' : job.title,
        'description' : job.description,
        'location' : job.location,
        'categories' : categories,
        'in_my_jobs' : in_my_jobs,
        'created_by_me' : created_by_me,
    }
    return render(request,"edit_job.html", context)

def update_job_api(request):
    user = get_logged_in_user(request)
    print(f"in update_job_api, user {user}")
    print(request)
    response = {
        'status' : 'unknown',
        'message' : 'unknown status'
    }
    if request.method == "POST":
        print(f"in update_job_api POST block")
        try:
            job_id = int(request.POST["job_id"])
            job_title = request.POST["job_title"]
            job_description = request.POST["job_description"]
            job_location = request.POST["job_location"]
            validation_errors = models.Job.objects.validate(job_title, job_description, job_location)
            print(f"validation_errors: {validation_errors}")
            if len(validation_errors)>0:
                print(f"validation_errors found")
                error_string = ",".join(validation_errors)
                response['status'] = "failed"
                response['message'] = error_string
            else:
                print(f"Calling job get for job_id:{job_id}")
                job = models.Job.objects.get(id = job_id)
                print(f"in update_job_api POST block, updating job: {job}")
                job.title = job_title
                job.description = job_description
                job.location = job_location
                job.save()
                job_categories_string = request.POST["job_categories_string"]
                if (job_categories_string > " "):
                    job_categories = job_categories_string.split(",")
                    for cat in models.JobCategory.objects.all():
                        if cat.category in job_categories:
                            print(f"Adding category [{cat.category}]")
                            job.categories.add(cat)
                        job.save()
                response["status"] = "succeeded"
                response["message"] = f"Updated Job with Title=[{job_title}]."
        except:
            response['status'] = "failed"
            response['message'] = str(sys.exc_info()[0])
    return JsonResponse(response)