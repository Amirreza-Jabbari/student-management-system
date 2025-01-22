from django import forms
from django.forms import Form
from student_management_app.models import Courses, SessionYearModel, CustomUser

class DateInput(forms.DateInput):
    input_type = "date"

class AddStudentForm(forms.Form):
    email = forms.EmailField(label="ایمیل", max_length=50, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="رمز عبور", max_length=50, widget=forms.PasswordInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label="نام", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="نام خانوادگی", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label="نام کاربری", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    address = forms.CharField(label="آدرس", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))

    gender_list = (
        ('Male', 'مرد'),
        ('Female', 'زن')
    )
    
    gender = forms.ChoiceField(
        label="جنسیت", 
        choices=gender_list, 
        widget=forms.Select(attrs={"class": "form-control"})
    )
    profile_pic = forms.FileField(label="عکس پروفایل", required=False, widget=forms.FileInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super(AddStudentForm, self).__init__(*args, **kwargs)
        
        # Multiple course selection
        self.fields['courses'] = forms.ModelMultipleChoiceField(
            queryset=Courses.objects.all(),
            widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            label="دروس",
            required=True
        )
        
        # Session year selection
        self.fields['session_year_id'].choices = [
            (session_year.id, f"{session_year.session_start_year} تا {session_year.session_end_year}") 
            for session_year in SessionYearModel.objects.all()
        ]

    session_year_id = forms.ChoiceField(label="سال تحصیلی", widget=forms.Select(attrs={"class": "form-control"}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("این نام کاربری قبلاً استفاده شده است")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً استفاده شده است")
        return email


class EditStudentForm(forms.Form):
    email = forms.EmailField(label="ایمیل", max_length=50, widget=forms.EmailInput(attrs={"class":"form-control"}))
    first_name = forms.CharField(label="نام", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name = forms.CharField(label="نام خانوادگی", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
    username = forms.CharField(label="نام کاربری", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
    address = forms.CharField(label="آدرس", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))

    gender_list = (
        ('Male', 'مرد'),
        ('Female', 'زن')
    )
    
    gender = forms.ChoiceField(
        label="جنسیت", 
        choices=gender_list, 
        widget=forms.Select(attrs={"class": "form-control"})
    )
    profile_pic = forms.FileField(label="عکس پروفایل", required=False, widget=forms.FileInput(attrs={"class":"form-control"}))

    def __init__(self, *args, **kwargs):
        super(EditStudentForm, self).__init__(*args, **kwargs)
        
        # Multiple course selection for editing
        self.fields['courses'] = forms.ModelMultipleChoiceField(
            queryset=Courses.objects.all(),
            widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            label="دروس",
            required=True
        )
        
        # Session year selection
        self.fields['session_year_id'].choices = [
            (session_year.id, f"{session_year.session_start_year} تا {session_year.session_end_year}") 
            for session_year in SessionYearModel.objects.all()
        ]

    session_year_id = forms.ChoiceField(label="سال تحصیلی", widget=forms.Select(attrs={"class":"form-control"}))