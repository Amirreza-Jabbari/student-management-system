from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import json


from student_management_app.models import CustomUser, Staffs, Courses, Subjects, Students, SessionYearModel, Attendance, AttendanceReport, LeaveReportStaff, FeedBackStaffs, StudentResult


def staff_home(request):
    # Fetching All Students under Staff
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    
    # Get unique courses for the subjects taught by this staff
    courses = Courses.objects.filter(subjects__in=subjects).distinct()
    
    # Count students in these courses
    students_count = Students.objects.filter(courses__in=courses).distinct().count()
    
    subject_count = subjects.count()

    # Fetch All Attendance Count
    attendance_count = Attendance.objects.filter(subject_id__in=subjects).count()
    
    # Fetch All Approve Leave
    staff = Staffs.objects.get(admin=request.user.id)
    leave_count = LeaveReportStaff.objects.filter(staff_id=staff.id, leave_status=1).count()

    # Fetch Attendance Data by Subjects
    subject_list = []
    attendance_list = []
    for subject in subjects:
        attendance_count1 = Attendance.objects.filter(subject_id=subject.id).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count1)

    # Get students in the courses taught by this staff
    students_attendance = Students.objects.filter(courses__in=courses).distinct()
    
    student_list = []
    student_list_attendance_present = []
    student_list_attendance_absent = []
    
    for student in students_attendance:
        attendance_present_count = AttendanceReport.objects.filter(status=True, student_id=student.id).count()
        attendance_absent_count = AttendanceReport.objects.filter(status=False, student_id=student.id).count()
        
        student_list.append(student.admin.first_name + " " + student.admin.last_name)
        student_list_attendance_present.append(attendance_present_count)
        student_list_attendance_absent.append(attendance_absent_count)

    context = {
        "students_count": students_count,
        "attendance_count": attendance_count,
        "leave_count": leave_count,
        "subject_count": subject_count,
        "subject_list": subject_list,
        "attendance_list": attendance_list,
        "student_list": student_list,
        "attendance_present_list": student_list_attendance_present,
        "attendance_absent_list": student_list_attendance_absent
    }
    
    return render(request, "staff_template/staff_home_template.html", context)


def staff_take_attendance(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "staff_template/take_attendance_template.html", context)


def staff_apply_leave(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    leave_data = LeaveReportStaff.objects.filter(staff_id=staff_obj)
    context = {
        "leave_data": leave_data
    }
    return render(request, "staff_template/staff_apply_leave_template.html", context)


def staff_apply_leave_save(request):
    if request.method != "POST":
        messages.error(request, "روش نامعتبر است.")
        return redirect('staff_apply_leave')
    else:
        leave_date = request.POST.get('leave_date')
        leave_message = request.POST.get('leave_message')

        staff_obj = Staffs.objects.get(admin=request.user.id)
        try:
            leave_report = LeaveReportStaff(staff_id=staff_obj, leave_date=leave_date, leave_message=leave_message, leave_status=0)
            leave_report.save()
            messages.success(request, "درخواست مرخصی با موفقیت ثبت شد!")
            return redirect('staff_apply_leave')
        except:
            messages.error(request, "درخواست مرخصی ناموفق بود.")
            return redirect('staff_apply_leave')


def staff_feedback(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    feedback_data = FeedBackStaffs.objects.filter(staff_id=staff_obj)
    context = {
        "feedback_data":feedback_data
    }
    return render(request, "staff_template/staff_feedback_template.html", context)


def staff_feedback_save(request):
    if request.method != "POST":
        messages.error(request, "روش نامعتبر است.")
        return redirect('staff_feedback')
    else:
        feedback = request.POST.get('feedback_message')
        staff_obj = Staffs.objects.get(admin=request.user.id)

        try:
            add_feedback = FeedBackStaffs(staff_id=staff_obj, feedback=feedback, feedback_reply="")
            add_feedback.save()
            messages.success(request, "بازخورد ارسال شد.")
            return redirect('staff_feedback')
        except:
            messages.error(request, "ارسال بازخورد ناموفق بود.")
            return redirect('staff_feedback')


# WE don't need csrf_token when using Ajax
@csrf_exempt
def get_students(request):
    # Getting Values from Ajax POST 'Fetch Student'
    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year")

    # Get the subject and session
    subject_model = Subjects.objects.get(id=subject_id)
    session_model = SessionYearModel.objects.get(id=session_year)

    # Find students in the course associated with this subject
    students = Students.objects.filter(
        courses=subject_model.course_id, 
        session_year_id=session_model
    )

    # Only Passing Student Id and Student Name Only
    list_data = []

    for student in students:
        data_small = {
            "id": student.admin.id, 
            "name": student.admin.first_name + " " + student.admin.last_name
        }
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)

@csrf_exempt
def save_attendance_data(request):
    try:
        # Get Values from Staff Take Attendance form via AJAX
        student_ids = request.POST.get("student_ids")
        subject_id = request.POST.get("subject_id")
        attendance_date = request.POST.get("attendance_date")
        session_year_id = request.POST.get("session_year_id")

        # Validate inputs
        if not all([student_ids, subject_id, attendance_date, session_year_id]):
            return HttpResponse("خطا: اطلاعات ناقص است")

        # Get model instances
        try:
            subject_model = Subjects.objects.get(id=subject_id)
            session_year_model = SessionYearModel.objects.get(id=session_year_id)
        except (Subjects.DoesNotExist, SessionYearModel.DoesNotExist):
            return HttpResponse("خطا: موضوع یا سال تحصیلی یافت نشد")

        # Parse student data
        try:
            json_student = json.loads(student_ids)
        except json.JSONDecodeError:
            return HttpResponse("خطا: فرمت داده‌های دانشجو نامعتبر است")

        # First Attendance Data is Saved on Attendance Model
        attendance = Attendance.objects.create(
            subject_id=subject_model, 
            attendance_date=attendance_date, 
            session_year_id=session_year_model
        )

        # Save attendance reports for each student
        for stud in json_student:
            try:
                student = Students.objects.get(admin_id=stud['id'])
                AttendanceReport.objects.create(
                    student_id=student, 
                    attendance_id=attendance, 
                    status=stud['status']
                )
            except Students.DoesNotExist:
                # Log the error or handle it as needed
                return HttpResponse(f"خطا: دانشجو با شناسه {stud['id']} یافت نشد")

        return HttpResponse("OK")

    except Exception as e:
        # Log the error for debugging
        print(f"Error in save_attendance_data: {str(e)}")
        return HttpResponse("خطا در ذخیره سازی")

def staff_update_attendance(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "staff_template/update_attendance_template.html", context)

@csrf_exempt
def get_attendance_dates(request):
    # Getting Values from Ajax POST 'Fetch Student'
    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year_id")

    # Students enroll to Course, Course has Subjects
    # Getting all data from subject model based on subject_id
    subject_model = Subjects.objects.get(id=subject_id)

    session_model = SessionYearModel.objects.get(id=session_year)

    # students = Students.objects.filter(course_id=subject_model.course_id, session_year_id=session_model)
    attendance = Attendance.objects.filter(subject_id=subject_model, session_year_id=session_model)

    # Only Passing Student Id and Student Name Only
    list_data = []

    for attendance_single in attendance:
        data_small={"id":attendance_single.id, "attendance_date":str(attendance_single.attendance_date), "session_year_id":attendance_single.session_year_id.id}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
def get_attendance_student(request):
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


@csrf_exempt
def update_attendance_data(request):
    try:
        # Get data from the request
        student_ids = request.POST.get("student_ids")
        attendance_date = request.POST.get("attendance_date")

        # Validate inputs
        if not student_ids or not attendance_date:
            return HttpResponse("خطا: اطلاعات ناقص است")

        # Get the specific attendance record
        try:
            attendance = Attendance.objects.get(id=attendance_date)
        except Attendance.DoesNotExist:
            return HttpResponse("خطا: رکورد حضور و غیاب یافت نشد")

        # Parse student data
        try:
            json_student = json.loads(student_ids)
        except json.JSONDecodeError:
            return HttpResponse("خطا: فرمت داده‌های دانشجو نامعتبر است")

        # Update attendance for each student
        for stud in json_student:
            try:
                # Find the specific student
                student = Students.objects.get(admin_id=stud['id'])
                
                # Find or create the attendance report
                attendance_report, created = AttendanceReport.objects.get_or_create(
                    student_id=student, 
                    attendance_id=attendance,
                    defaults={'status': stud['status']}
                )
                
                # Update the status if the report already exists
                if not created:
                    attendance_report.status = stud['status']
                    attendance_report.save()
                
            except (Students.DoesNotExist, Exception) as e:
                # Log the error or handle it as needed
                print(f"Error updating attendance for student {stud['id']}: {str(e)}")
                return HttpResponse(f"خطا: به‌روزرسانی برای دانشجو با شناسه {stud['id']} ناموفق بود")

        return HttpResponse("OK")

    except Exception as e:
        # Log the error for debugging
        print(f"Error in update_attendance_data: {str(e)}")
        return HttpResponse("خطا در به‌روزرسانی")

def staff_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)

    context={
        "user": user,
        "staff": staff
    }
    return render(request, 'staff_template/staff_profile.html', context)


def staff_profile_update(request):
    if request.method != "POST":
        messages.error(request, "روش نامعتبر است.")
        return redirect('staff_profile')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        address = request.POST.get('address')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()

            staff = Staffs.objects.get(admin=customuser.id)
            staff.address = address
            staff.save()

            messages.success(request, "پروفایل شما با موفقیت به‌روز شد.")
            return redirect('staff_profile')
        except:
            messages.error(request, "بروزرسانی پروفایل ناموفق بود.")
            return redirect('staff_profile')



def staff_add_result(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years,
    }
    return render(request, "staff_template/add_result_template.html", context)


def staff_add_result_save(request):
    if request.method != "POST":
        messages.error(request, "روش نامعتبر است.")
        return redirect('staff_add_result')
    else:
        student_admin_id = request.POST.get('student_list')
        assignment_marks = request.POST.get('assignment_marks')
        exam_marks = request.POST.get('exam_marks')
        subject_id = request.POST.get('subject')

        student_obj = Students.objects.get(admin=student_admin_id)
        subject_obj = Subjects.objects.get(id=subject_id)

        try:
            # Check if Students Result Already Exists or not
            check_exist = StudentResult.objects.filter(subject_id=subject_obj, student_id=student_obj).exists()
            if check_exist:
                result = StudentResult.objects.get(subject_id=subject_obj, student_id=student_obj)
                result.subject_assignment_marks = assignment_marks
                result.subject_exam_marks = exam_marks
                result.save()
                messages.success(request, "Result Updated Successfully!")
                return redirect('staff_add_result')
            else:
                result = StudentResult(student_id=student_obj, subject_id=subject_obj, subject_exam_marks=exam_marks, subject_assignment_marks=assignment_marks)
                result.save()
                messages.success(request, "Result Added Successfully!")
                return redirect('staff_add_result')
        except:
            messages.error(request, "Failed to Add Result!")
            return redirect('staff_add_result')
