# from channels.auth import login, logout
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from student_management_app.EmailBackEnd import EmailBackEnd

def home(request):
    return render(request, 'index.html')

def loginPage(request):
    return render(request, 'login.html')

def doLogin(request):
    if request.method != "POST":
        return HttpResponse("<h2>روش مجاز نیست</h2>")
    else:
        user = EmailBackEnd.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            user_type = user.user_type
            #return HttpResponse("Email: "+request.POST.get('email')+ " Password: "+request.POST.get('password'))
            if user_type == '1':
                return redirect('admin_home')
                
            elif user_type == '2':
                # return HttpResponse("Staff Login")
                return redirect('staff_home')
                
            elif user_type == '3':
                # return HttpResponse("Student Login")
                return redirect('student_home')
            else:
                messages.error(request, "ورود نامعتبر!")
                return redirect('login')
        else:
            messages.error(request, "رمز ورود یا ایمیل اشتباه است")
            #return HttpResponseRedirect("/")
            return redirect('login')


def get_user_details(request):
    if request.user != None:
        return HttpResponse("کاربر: "+request.user.email+" نوع کاربر: "+request.user.user_type)
    else:
        return HttpResponse("لطفاً ابتدا وارد شوید")

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')