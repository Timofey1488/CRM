from django import forms


class MyForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))