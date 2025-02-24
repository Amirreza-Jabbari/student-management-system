from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import json
from django.db import transaction
from student_management_app.models import CustomUser, Staffs, Courses, Subjects, Students, SessionYearModel, FeedBackStudent, FeedBackStaffs, LeaveReportStudent, LeaveReportStaff, Attendance, AttendanceReport, StaffAttendance
from .forms import AddStudentForm, EditStudentForm
import pandas as pd
import jdatetime

def admin_home(request):
    try:
        # Student Count
        all_student_count = Students.objects.all().count()
        
        # Staff Count
        staff_count = Staffs.objects.all().count()
        
        # Course Count
        course_count = Courses.objects.all().count()
        
        # Subject Count
        subject_count = Subjects.objects.all().count()
        
        # Course Names
        course_name_list = list(Courses.objects.values_list('course_name', flat=True))
        
        # Subject Count in Each Course
        subject_count_list = [
            Subjects.objects.filter(course_id=course).count() 
            for course in Courses.objects.all()
        ]
        
        # Students Count in Each Course
        student_count_list_in_course = [
            Students.objects.filter(courses=course).count() 
            for course in Courses.objects.all()
        ]
        
        # Students Count in Each Subject
        subjects = Subjects.objects.all()
        subject_list = list(subjects.values_list('subject_name', flat=True))
        
        # Optimize student count in subjects
        student_count_list_in_subject = []
        for subject in subjects:
            student_count = subject.students.count()
            student_count_list_in_subject.append(student_count)
        
        # Staff Attendance Calculations
        staff_attendance_present_list = []
        staff_attendance_leave_list = []
        staff_name_list = []
        
        staffs = Staffs.objects.select_related('admin').all()
        for staff in staffs:
            staff_name_list.append(staff.admin.username)
            
            # Get all attendances for this staff
            staff_attendances = Attendance.objects.filter(subject_id__staff_id=staff.admin)
            
            present_count = 0
            leave_count = 0
            
            for attendance in staff_attendances:
                attendance_reports = AttendanceReport.objects.filter(attendance_id=attendance)
                present_count += attendance_reports.filter(status=True).count()
                leave_count += attendance_reports.filter(status=False).count()
            
            staff_attendance_present_list.append(present_count)
            staff_attendance_leave_list.append(leave_count)
        
        # Student Attendance Calculations
        student_attendance_present_list = []
        student_attendance_leave_list = []
        student_name_list = []
        
        students = Students.objects.select_related('admin').all()
        for student in students:
            student_name_list.append(student.admin.username)
            
            # Get all attendances for this student
            student_attendances = AttendanceReport.objects.filter(student_id=student)
            
            present_count = student_attendances.filter(status=True).count()
            leave_count = student_attendances.filter(status=False).count()
            
            student_attendance_present_list.append(present_count)
            student_attendance_leave_list.append(leave_count)
        
        # Prepare context
        context = {
            'all_student_count': all_student_count,
            'staff_count': staff_count,
            'course_count': course_count,
            'subject_count': subject_count,
            'course_name_list': course_name_list,
            'subject_count_list': subject_count_list,
            'student_count_list_in_course': student_count_list_in_course,
            'subject_list': subject_list,
            'student_count_list_in_subject': student_count_list_in_subject,
            'staff_attendance_present_list': staff_attendance_present_list,
            'staff_attendance_leave_list': staff_attendance_leave_list,
            'staff_name_list': staff_name_list,
            'student_attendance_present_list': student_attendance_present_list,
            'student_attendance_leave_list': student_attendance_leave_list,
            'student_name_list': student_name_list,
        }
        
        return render(request, 'hod_template/home_content.html', context)
    
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in admin_home: {str(e)}")
        
        # Optionally, you can add a custom error handling
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('some_error_page')  # Replace with appropriate error handling
        
def add_staff(request):
    return render(request, "hod_template/add_staff_template.html")


def add_staff_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method ")
        return redirect('add_staff')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        address = request.POST.get('address')

        try:
            user = CustomUser.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name, user_type=2)
            user.staffs.address = address
            user.save()
            messages.success(request, "استاد با موفقیت افزوده شد!")
            return redirect('add_staff')
        except:
            messages.error(request, "خطا در افزودن استاد")
            return redirect('add_staff')

def manage_staff(request):
    staffs = Staffs.objects.all()
    context = {
        "staffs": staffs
    }
    return render(request, "hod_template/manage_staff_template.html", context)


def edit_staff(request, staff_id):
    staff = Staffs.objects.get(admin=staff_id)

    context = {
        "staff": staff,
        "id": staff_id
    }
    return render(request, "hod_template/edit_staff_template.html", context)


def edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id = request.POST.get('staff_id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')

        try:
            # INSERTING into Customuser Model
            user = CustomUser.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.save()
            
            # INSERTING into Staff Model
            staff_model = Staffs.objects.get(admin=staff_id)
            staff_model.address = address
            staff_model.save()

            messages.success(request, "اطلاعات استاد با موفقیت به روز رسانی شد!")
            return redirect('/edit_staff/'+staff_id)

        except:
            messages.error(request, "خطا در به روز رسانی اطلاعات استاد")
            return redirect('/edit_staff/'+staff_id)

def delete_staff(request, staff_id):
    staff = Staffs.objects.get(admin=staff_id)
    try:
        staff.delete()
        messages.success(request, "استاد با موفقیت حذف شد!")
        return redirect('manage_staff')
    except:
        messages.error(request, "خطا در حذف استاد.")
        return redirect('manage_staff')

def add_course(request):
    return render(request, "hod_template/add_course_template.html")

def add_course_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('add_course')
    else:
        course = request.POST.get('course')
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "درس با موفقیت افزوده شد!")
            return redirect('add_course')
        except:
            messages.error(request, "خطا در افزودن درس.")
            return redirect('add_course')


def manage_course(request):
    courses = Courses.objects.all()
    context = {
        "courses": courses
    }
    return render(request, 'hod_template/manage_course_template.html', context)


def edit_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    context = {
        "course": course,
        "id": course_id
    }
    return render(request, 'hod_template/edit_course_template.html', context)


def edit_course_save(request):
    if request.method != "POST":
        HttpResponse("Invalid Method")
    else:
        course_id = request.POST.get('course_id')
        course_name = request.POST.get('course')

        try:
            course = Courses.objects.get(id=course_id)
            course.course_name = course_name
            course.save()

            messages.success(request, "اطلاعات درس با موفقیت به روز رسانی شد!")
            return redirect('/edit_course/'+course_id)

        except:
            messages.error(request, "خطا در به روز رسانی درس.")
            return redirect('/edit_course/'+course_id)


def delete_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    try:
        course.delete()
        messages.success(request, "درس با موفقیت حذف شد!")
        return redirect('manage_course')
    except:
        messages.error(request, "خطا در حذف درس")
        return redirect('manage_course')


def manage_session(request):
    session_years = SessionYearModel.objects.all()
    context = {
        "session_years": session_years
    }
    return render(request, "hod_template/manage_session_template.html", context)


def add_session(request):
    return render(request, "hod_template/add_session_template.html")


def add_session_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('add_course')
    else:
        session_start_year = request.POST.get('session_start_year')
        session_end_year = request.POST.get('session_end_year')

        try:
            sessionyear = SessionYearModel(session_start_year=session_start_year, session_end_year=session_end_year)
            sessionyear.save()
            messages.success(request, "ترم تحصیلی با موفقیت ایجاد شد!")
            return redirect("add_session")
        except:
            messages.error(request, "خطا در افزودن ترم تحصیلی")
            return redirect("add_session")


def edit_session(request, session_id):
    session_year = SessionYearModel.objects.get(id=session_id)
    context = {
        "session_year": session_year
    }
    return render(request, "hod_template/edit_session_template.html", context)


def edit_session_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('manage_session')
    else:
        session_id = request.POST.get('session_id')
        session_start_year = request.POST.get('session_start_year')
        session_end_year = request.POST.get('session_end_year')

        try:
            session_year = SessionYearModel.objects.get(id=session_id)
            session_year.session_start_year = session_start_year
            session_year.session_end_year = session_end_year
            session_year.save()

            messages.success(request, "تغییرات ترم تحصیلی با موفقیت ذخیره شد!")
            return redirect('/edit_session/'+session_id)
        except:
            messages.error(request, "خطا در به روز رسانی تغییرات ترم تحصیلی.")
            return redirect('/edit_session/'+session_id)


def delete_session(request, session_id):
    session = SessionYearModel.objects.get(id=session_id)
    try:
        session.delete()
        messages.success(request, "ترم تحصیلی با موفقیت حذف شد!")
        return redirect('manage_session')
    except:
        messages.error(request, "خطا در حذف ترم تحصیلی")
        return redirect('manage_session')


def add_student(request):
    form = AddStudentForm()
    context = {
        "form": form
    }
    return render(request, 'hod_template/add_student_template.html', context)

def add_student_save(request):
    if request.method != "POST":
        messages.error(request, "روش درخواست نامعتبر است")
        return redirect('add_student')
    
    form = AddStudentForm(request.POST, request.FILES)

    if form.is_valid():
        try:
            # Start database transaction
            with transaction.atomic():
                # First, check if a student with this user already exists
                username = form.cleaned_data['username']
                existing_user = CustomUser.objects.filter(username=username).first()
                
                if existing_user:
                    # If user exists, check if they're already a student
                    if hasattr(existing_user, 'students'):
                        messages.error(request, "این کاربر قبلاً به عنوان دانشجو ثبت شده است.")
                        return redirect('add_student')
                    
                    # If user exists but not a student, update their type
                    existing_user.user_type = 3
                    existing_user.save()
                else:
                    # Create new CustomUser
                    existing_user = CustomUser.objects.create_user(
                        username=username, 
                        password=form.cleaned_data['password'], 
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'], 
                        last_name=form.cleaned_data['last_name'], 
                        user_type=3
                    )

                # Get or create session year
                session_year = SessionYearModel.objects.get(id=form.cleaned_data['session_year_id'])
                
                # Try to get existing student, or create new
                try:
                    student = Students.objects.get(admin=existing_user)
                    # Update existing student if needed
                    student.address = form.cleaned_data['address']
                    student.gender = form.cleaned_data['gender'].lower()
                    student.session_year_id = session_year
                    if 'profile_pic' in request.FILES:
                        student.profile_pic = request.FILES['profile_pic']
                    student.save()
                except Students.DoesNotExist:
                    # Create new student only if doesn't exist
                    student = Students.objects.create(
                        admin=existing_user,
                        address=form.cleaned_data['address'],
                        gender=form.cleaned_data['gender'].lower(),
                        profile_pic=request.FILES.get('profile_pic', None),
                        session_year_id=session_year
                    )
                
                # Add courses
                student.courses.set(form.cleaned_data['courses'])
                
                messages.success(request, "دانشجو با موفقیت اضافه شد")
                return redirect('add_student')

        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full traceback
            messages.error(request, f"خطای سیستمی در افزودن دانشجو: {str(e)}")
            return redirect('add_student')

    # If form is invalid
    context = {
        "form": form
    }
    return render(request, 'hod_template/add_student_template.html', context)
                                    
def manage_student(request):
    students = Students.objects.all()
    # Add debugging print
    for student in students:
        print(f"Student: {student.admin.username}, Gender: {student.gender}")
    
    context = {
        "students": students
    }
    return render(request, 'hod_template/manage_student_template.html', context)


def edit_student(request, student_id):
    # Adding Student ID into Session Variable
    request.session['student_id'] = student_id

    student = Students.objects.get(admin=student_id)
    form = EditStudentForm()
    
    # Filling the form with Data from Database
    form.fields['email'].initial = student.admin.email
    form.fields['username'].initial = student.admin.username
    form.fields['first_name'].initial = student.admin.first_name
    form.fields['last_name'].initial = student.admin.last_name
    form.fields['address'].initial = student.address
    form.fields['gender'].initial = student.gender
    form.fields['session_year_id'].initial = student.session_year_id.id
    
    # Set initial courses
    form.fields['courses'].initial = student.courses.all()

    context = {
        "id": student_id,
        "username": student.admin.username,
        "form": form
    }
    return render(request, "hod_template/edit_student_template.html", context)

def edit_student_save(request):
    if request.method != "POST":
        return HttpResponse("Invalid Method!")
    else:
        student_id = request.session.get('student_id')
        if student_id == None:
            return redirect('/manage_student')

        form = EditStudentForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            address = form.cleaned_data['address']
            courses = form.cleaned_data['courses']  # Multiple courses
            gender = form.cleaned_data['gender']
            session_year_id = form.cleaned_data['session_year_id']

            # Profile pic handling
            if len(request.FILES) != 0:
                profile_pic = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                profile_pic_url = fs.url(filename)
            else:
                profile_pic_url = None

            try:
                with transaction.atomic():
                    # Update CustomUser
                    user = CustomUser.objects.get(id=student_id)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.username = username
                    user.save()

                    # Update Students
                    student_model = Students.objects.get(admin=student_id)
                    student_model.address = address
                    student_model.gender = gender
                    
                    # Update session year
                    session_year_obj = SessionYearModel.objects.get(id=session_year_id)
                    student_model.session_year_id = session_year_obj

                    # Update profile pic if new one is uploaded
                    if profile_pic_url:
                        student_model.profile_pic = profile_pic_url
                    
                    student_model.save()

                    # Update courses
                    student_model.courses.set(courses)

                    # Delete student_id SESSION
                    del request.session['student_id']

                    messages.success(request, "اطلاعات دانشجو با موفقیت به روز رسانی شد!")
                    return redirect('/edit_student/'+student_id)
            
            except Exception as e:
                messages.error(request, f"خطا در به روز رسانی اطلاعات دانشجو: {str(e)}")
                return redirect('/edit_student/'+student_id)
        else:
            return redirect('/edit_student/'+student_id)

def delete_student(request, student_id):
    student = Students.objects.get(admin=student_id)
    try:
        student.delete()
        messages.success(request, "دانشحو با موفقیت حذف شد!")
        return redirect('manage_student')
    except:
        messages.error(request, "خطا در حذف دانشجو.")
        return redirect('manage_student')


def add_subject(request):
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type='2')
    context = {
        "courses": courses,
        "staffs": staffs
    }
    return render(request, 'hod_template/add_subject_template.html', context)


def add_subject_save(request):
    if request.method != "POST":
        messages.error(request, "Method Not Allowed!")
        return redirect('add_subject')
    else:
        subject_name = request.POST.get('subject')

        course_id = request.POST.get('course')
        course = Courses.objects.get(id=course_id)
        
        staff_id = request.POST.get('staff')
        staff = CustomUser.objects.get(id=staff_id)

        try:
            subject = Subjects(subject_name=subject_name, course_id=course, staff_id=staff)
            subject.save()
            messages.success(request, "واحد درسی با موفقیت ثبت شد!")
            return redirect('add_subject')
        except:
            messages.error(request, "خطا در ثبت واحد درسی")
            return redirect('add_subject')


def manage_subject(request):
    subjects = Subjects.objects.all()
    context = {
        "subjects": subjects
    }
    return render(request, 'hod_template/manage_subject_template.html', context)


def edit_subject(request, subject_id):
    subject = Subjects.objects.get(id=subject_id)
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type='2')
    context = {
        "subject": subject,
        "courses": courses,
        "staffs": staffs,
        "id": subject_id
    }
    return render(request, 'hod_template/edit_subject_template.html', context)


def edit_subject_save(request):
    if request.method != "POST":
        HttpResponse("Invalid Method.")
    else:
        subject_id = request.POST.get('subject_id')
        subject_name = request.POST.get('subject')
        course_id = request.POST.get('course')
        staff_id = request.POST.get('staff')

        try:
            subject = Subjects.objects.get(id=subject_id)
            subject.subject_name = subject_name

            course = Courses.objects.get(id=course_id)
            subject.course_id = course

            staff = CustomUser.objects.get(id=staff_id)
            subject.staff_id = staff
            
            subject.save()

            messages.success(request, "واحد درسی با موفقیت به روز رسانی شد!")
            # return redirect('/edit_subject/'+subject_id)
            return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id":subject_id}))

        except:
            messages.error(request, "خطا در ذخیره ی تغییرات واحد درسی")
            return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id":subject_id}))
            # return redirect('/edit_subject/'+subject_id)


def delete_subject(request, subject_id):
    subject = Subjects.objects.get(id=subject_id)
    try:
        subject.delete()
        messages.success(request, "واحد درسی با موفقیت حذف شد!")
        return redirect('manage_subject')
    except:
        messages.error(request, "خطا در حذف واحد درسی")
        return redirect('manage_subject')


@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_obj = CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def student_feedback_message(request):
    feedbacks = FeedBackStudent.objects.all()
    context = {
        "feedbacks": feedbacks
    }
    return render(request, 'hod_template/student_feedback_template.html', context)


@csrf_exempt
def student_feedback_message_reply(request):
    feedback_id = request.POST.get('id')
    feedback_reply = request.POST.get('reply')

    try:
        feedback = FeedBackStudent.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_reply
        feedback.save()
        return HttpResponse("True")

    except:
        return HttpResponse("False")


def staff_feedback_message(request):
    feedbacks = FeedBackStaffs.objects.all()
    context = {
        "feedbacks": feedbacks
    }
    return render(request, 'hod_template/staff_feedback_template.html', context)


@csrf_exempt
def staff_feedback_message_reply(request):
    feedback_id = request.POST.get('id')
    feedback_reply = request.POST.get('reply')

    try:
        feedback = FeedBackStaffs.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_reply
        feedback.save()
        return HttpResponse("True")

    except:
        return HttpResponse("False")


def student_leave_view(request):
    leaves = LeaveReportStudent.objects.all()
    context = {
        "leaves": leaves
    }
    return render(request, 'hod_template/student_leave_view.html', context)

def student_leave_approve(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return redirect('student_leave_view')


def student_leave_reject(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return redirect('student_leave_view')


def staff_leave_view(request):
    leaves = LeaveReportStaff.objects.all()
    context = {
        "leaves": leaves
    }
    return render(request, 'hod_template/staff_leave_view.html', context)


def staff_leave_approve(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return redirect('staff_leave_view')


def staff_leave_reject(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return redirect('staff_leave_view')


def admin_view_attendance(request):
    subjects = Subjects.objects.all()
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "hod_template/admin_view_attendance.html", context)


@csrf_exempt
def admin_get_attendance_dates(request):
    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year_id")

    subject_model = Subjects.objects.get(id=subject_id)
    session_model = SessionYearModel.objects.get(id=session_year)

    attendance = Attendance.objects.filter(subject_id=subject_model, session_year_id=session_model)

    list_data = []

    for attendance_single in attendance:
        persian_date = jdatetime.date.fromgregorian(date=attendance_single.attendance_date)
        data_small = {
            "id": attendance_single.id,
            "attendance_date": str(persian_date),  # Convert to Persian date
            "session_year_id": attendance_single.session_year_id.id
        }
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
def admin_get_attendance_student(request):
    # Getting Values from Ajax POST 'Fetch Student'
    attendance_date = request.POST.get('attendance_date')
    attendance = Attendance.objects.get(id=attendance_date)

    attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
    # Only Passing Student Id and Student Name Only
    list_data = []

    for student in attendance_data:
        data_small={"id":student.student_id.admin.id, "name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name, "status":student.status}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


def admin_profile(request):
    user = CustomUser.objects.get(id=request.user.id)

    context={
        "user": user
    }
    return render(request, 'hod_template/admin_profile.html', context)


def admin_profile_update(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('admin_profile')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()
            messages.success(request, "پروفایل با موفقیت به روز رسانی شد!")
            return redirect('admin_profile')
        except:
            messages.error(request, "خطا در به روز رسانی پروفایل.")
            return redirect('admin_profile')
    
def staff_profile(request):
    pass

def student_profile(request):
    pass

def some_error_page(request):
    return render(request, 'hod_template/error_page.html')

def transliterate_to_english(persian_name):
    transliteration_dict = {
        'آ':'A', 'ا': 'A', 'ب': 'B', 'پ': 'P', 'ت': 'T', 'ث': 'S',
        'ج': 'J', 'چ': 'CH', 'ح': 'H', 'خ': 'KH', 'د': 'D', 'ذ': 'Z',
        'ر': 'R', 'ز': 'Z', 'ژ': 'ZH', 'س': 'S', 'ش': 'SH', 'ص': 'S',
        'ض': 'Z', 'ط': 'T', 'ظ': 'Z', 'ع': 'A', 'غ': 'GH', 'ف': 'F',
        'ق': 'GH', 'ک': 'K', 'گ': 'G', 'ل': 'L', 'م': 'M', 'ن': 'N',
        'و': 'o', 'ه': 'H', 'ی': 'I','ي': 'I', 'ئ': 'I'
    }
    
    # Convert each character to its English equivalent
    english_name = ''.join(transliteration_dict.get(char, char) for char in persian_name)
    
    return english_name

def import_excel(request):
    if request.method == 'POST':
        excel_file = request.FILES['excel_file']
        try:
            # Load the Excel file
            data = pd.read_excel(excel_file)

            # Loop through each row in the Excel file
            for _, row in data.iterrows():
                # Handle Course
                course_name = row['نام درس'].strip()
                course, _ = Courses.objects.get_or_create(course_name=course_name)

                # Handle Staff
                first_name_persian = row['نام\nاستاد'].strip()
                last_name_persian = row['نام خانوادگی\nاستاد'].strip()
                
                # Convert names to English (assuming you have a transliteration function)
                first_name_english = transliterate_to_english(first_name_persian)
                last_name_english = transliterate_to_english(last_name_persian)

                # Generate a unique username
                username = f"{first_name_english}_{last_name_english}".lower()  # Convert to lowercase for consistency

                # Set a default password
                password = '1234567890'

                # Check if the username already exists
                custom_user, created = CustomUser .objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name_persian,
                        'last_name': last_name_persian,
                        'email': f"{username}@example.com",  # You might want to generate a proper email
                        'user_type': 2  # Setting user type as Staff
                    }
                )

                # If the user was created, set the password
                if created:
                    custom_user.set_password(password)  # Set the password
                    custom_user.save()

                # Handle Staff
                staff, _ = Staffs.objects.get_or_create(admin=custom_user)

                # Handle Subject
                subject_name = row['نام درس'].strip()
                Subjects.objects.get_or_create(
                    subject_name=subject_name,
                    course_id=course,
                    staff_id=custom_user
                )

            messages.success(request, "اطلاعات با موفقیت وارد شد!")
            return redirect('manage_staff')  # Redirect to manage staff page

        except Exception as e:
            messages.error(request, f"خطا در وارد کردن اطلاعات: {str(e)}")
            return redirect('manage_staff')

    return render(request, 'hod_template/manage_staff_template.html')  # Render the same page if not POST


def staff_attendance_home(request):
    staffs = Staffs.objects.all()
    context = {
        "staffs": staffs
    }
    return render(request, 'hod_template/staff_attendance_home.html', context)

def take_staff_attendance(request):
    staffs = Staffs.objects.all()
    context = {
        "staffs": staffs
    }
    return render(request, 'hod_template/take_staff_attendance.html', context)

@csrf_exempt
def save_staff_attendance(request):
    if request.method != "POST":
        return HttpResponse("Invalid Method")
    
    try:
        # دریافت اطلاعات حضور و غیاب ارسال شده
        staff_data = request.POST.get('staff_data')
        attendance_date = request.POST.get('attendance_date')

        # تبدیل رشته JSON به لیست دیکشنری‌ها (هر دیکشنری شامل id، time_slot و status)
        staff_data = json.loads(staff_data)

        # ثبت یا به‌روزرسانی حضور و غیاب برای هر رکورد
        for record in staff_data:
            staff = Staffs.objects.get(admin_id=record['id'])
            
            attendance, created = StaffAttendance.objects.get_or_create(
                staff_id=staff,
                attendance_date=attendance_date,
                time_slot=record['time_slot'],
                defaults={'status': record['status']}
            )
            
            if not created:
                attendance.status = record['status']
                attendance.save()

        return HttpResponse("OK")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

def staff_attendance_view(request):
    # Get all staff attendance records
    staff_attendances = StaffAttendance.objects.all().order_by('-attendance_date')
    
    context = {
        "staff_attendances": staff_attendances
    }
    return render(request, 'hod_template/staff_attendance_view.html', context)

@csrf_exempt
def staff_attendance_filter(request):
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            staff_attendances = StaffAttendance.objects.filter(
                attendance_date__range=[start_date, end_date]
            ).order_by('-attendance_date')
            
            attendance_data = []
            for attendance in staff_attendances:
                attendance_data.append({
                    'staff_name': f"{attendance.staff_id.admin.first_name} {attendance.staff_id.admin.last_name}",
                    'date': str(attendance.attendance_date),
                    'time_slot': attendance.time_slot,
                    'status': 'حاضر' if attendance.status else 'غایب'
                })
            
            return JsonResponse({'data': attendance_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)