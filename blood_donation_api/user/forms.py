from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import RegexValidator
from .models import user, blood_group, address

class form_login(forms.Form):
    username = forms.CharField(
        label='Username',
        required=True, 
        max_length=32,
        help_text='Your username',
        widget=forms.TextInput(attrs={'placeholder':'Username'})
    )
    password = forms.CharField(
        label='Password',
        required=True,
        max_length=32,
        min_length=6,
        help_text='A strong password has combination of letters, numbers and characters',
        widget=forms.PasswordInput(attrs={'placeholder':'Password'})
    )
    # class Meta:
    #     model = user
    #     fields = ["username", "password"]

class form_register(forms.Form):
    #---------- Details of the User ----------#
    username = forms.CharField(
        label='Username', 
        required=True, 
        max_length=32,
        help_text='Your username',
        widget=forms.TextInput(attrs={'placeholder':'Username'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        help_text='Your email',
        max_length=42,
        widget=forms.EmailInput(attrs={'placeholder':'Email'})
    )
    password = forms.CharField(
        label='Password',
        required=True,
        max_length=32,
        min_length=6,
        help_text='A strong password has combination of letters, numbers and characters',
        widget=forms.PasswordInput(attrs={'placeholder':'Password'})
    )
    # ^\+?[1-9]\d{1,14}$
    # ^\+[1-9]\d{1,14}$
    e_164_phone_number_validator = RegexValidator(r'^\+[1-9]\d{1,14}$', 'Enter a valid E.164 compliant phone number', 'invalid')
    phone_number = forms.CharField(
        label='Phone',
        required=False,
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder':'Phone Number'}),
        validators=[e_164_phone_number_validator]  
    )
    choice_gender = [(0, 'Male'), (1, 'Female'), (2, 'Other')]
    gender = forms.ChoiceField(
        label='Gender',
        required=False,
        widget=forms.RadioSelect(attrs={'title':'Gender'}),
        choices=choice_gender
    )
    display_name = forms.CharField(
        label='Display Name', 
        required=False, 
        max_length=100,
        help_text='Your Display Name',
        widget=forms.TextInput(attrs={'placeholder':'Display Name'})
    )
    first_name = forms.CharField(
        label='First Name', 
        required=False, 
        max_length=20,
        help_text='Your first name',
        widget=forms.TextInput(attrs={'placeholder':'First Name'})
    )
    last_name = forms.CharField(
        label='Last Name', 
        required=False, 
        max_length=20,
        help_text='Your last name',
        widget=forms.TextInput(attrs={'placeholder':'Last Name'})
    )
    # class Meta:
    #     model = user
    #     fields = ["username", "email","password", "phone_number", "gender", "first_name", "last_name"]

class form_blood_group(forms.ModelForm):
    #---------- Blood Group of the User ----------#
    blood_group_name = forms.CharField(
        label='Blood Group',
        max_length=20, 
        required=False
    )

    class Meta:
        model = blood_group
        fields = ["blood_group_name"]

class form_address(forms.ModelForm):
    #---------- Address of the User ----------#
    area = forms.CharField(
        label='Area',
        max_length=20,
        required=False
    )
    city = forms.CharField(
        label='City',
        max_length=20,
        required=True
    )
    state = forms.CharField(
        label='State',
        max_length=20,
        required=True
    )
    zip = forms.IntegerField(
        label='Zip Code',
        required=False
    )
    country = forms.CharField(
        label='Country',
        max_length=20,
        required=True
    )

    class Meta:
        model = address
        fields = ["area", "city", "state", "zip", "country"]

class form_update(forms.Form):
    #---------- Details of the User ----------#
    username = forms.CharField(
        label='Username', 
        required=True, 
        max_length=32,
        help_text='Your username',
        widget=forms.TextInput(attrs={'placeholder':'Username'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        help_text='Your email',
        max_length=42,
        widget=forms.EmailInput(attrs={'placeholder':'Email'})
    )
    # ^\+?[1-9]\d{1,14}$
    e_164_phone_number_validator = RegexValidator(r'^\+?[1-9]\d{1,14}$', 'Enter a valid E.164 compliant number', 'invalid')
    phone_number = forms.CharField(
        label='Phone',
        required=False,
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder':'Phone Number'}),
        # validators=[e_164_phone_number_validator]  
    )
    choice_gender = [(0, 'Male'), (1, 'Female'), (2, 'Other')]
    gender = forms.ChoiceField(
        label='Gender',
        required=False,
        widget=forms.RadioSelect(attrs={'title':'Gender'}),
        choices=choice_gender
    )
    display_name = forms.CharField(
        label='Display Name', 
        required=False, 
        max_length=100,
        help_text='Your Display Name',
        widget=forms.TextInput(attrs={'placeholder':'Display Name'})
    )
    first_name = forms.CharField(
        label='First Name', 
        required=False, 
        max_length=20,
        help_text='Your first name',
        widget=forms.TextInput(attrs={'placeholder':'First Name'})
    )
    last_name = forms.CharField(
        label='Last Name', 
        required=False, 
        max_length=20,
        help_text='Your last name',
        widget=forms.TextInput(attrs={'placeholder':'Last Name'})
    )
    blood_group_name = forms.CharField(
        label='Blood Group',
        max_length=20, 
        required=False
    )
    area = forms.CharField(
        label='Area',
        max_length=20,
        required=False
    )
    city = forms.CharField(
        label='City',
        max_length=20,
        required=True
    )
    state = forms.CharField(
        label='State',
        max_length=20,
        required=True
    )
    zip = forms.IntegerField(
        label='Zip Code',
        required=False
    )
    country = forms.CharField(
        label='Country',
        max_length=20,
        required=True
    )

class form_addItem(forms.Form):
    username = forms.CharField(
        label='Username',
        max_length=20,
        required=True
    )
    name = forms.CharField(
        label='Item name',
        max_length=20,
        required=True
    )
    price = forms.CharField(
        label='Price',
        max_length=20,
        required=True
    )
    quantity = forms.IntegerField(
        label='Quantity',
        required=False
    )
    expiry_date = forms.CharField(
        label='Expiry Date',
        required=False
    )
    purchase_date = forms.CharField(
        label='Purchase Date',
        max_length=20,
        required=False
    )
    description = forms.CharField(
        label='Description',
        max_length=2000,
        required=False
    )

class form_getItems(forms.Form):
    username = forms.CharField(
        label='Username',
        max_length=20,
        required=True
    )

class form_sellItem(forms.Form):
    username = forms.CharField(
        label='Username',
        max_length=20,
        required=True
    )
    name = forms.CharField(
        label='Item name',
        max_length=20,
        required=True
    )
    price = forms.CharField(
        label='Price',
        max_length=20,
        required=True
    )
    available_quantity = forms.IntegerField(
        label='Quantity',
        required=True
    )
    quantity = forms.IntegerField(
        label='Quantity',
        required=True
    )
    expiry_date = forms.CharField(
        label='Expiry Date',
        required=False
    )
    purchase_date = forms.CharField(
        label='Purchase Date',
        max_length=20,
        required=False
    )
    description = forms.CharField(
        label='Description',
        max_length=2000,
        required=False
    )