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
        return redirect(reverse('home_view'))

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

def home_view(request):
    if "logged_in_user" in request.session:
        return render(request,"home_view.html")
    else:
        return redirect(reverse('signin_view'))

def user_level_control(value,is_admin,user_id):
    if is_admin:
        if value == "admin":
            return f"<select class='user_level_dropdown' user_id='{user_id}'><option value='admin' selected>admin</option><option value='normal'>normal</option></select>"
        else:
            return f"<select class='user_level_dropdown' user_id='{user_id}'><option class='user_level_dropdown' value='admin'>admin</option><option value='normal' selected>normal</option></select>"
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
    user = models.User.objects.get(id=int(user_id))
    context = {
        'user' : user
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

