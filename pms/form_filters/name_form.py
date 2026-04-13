from django import forms
class NameForm(forms.Form):
    name = forms.CharField(
            max_length=100,
        label="Nombre",
        required=True,
        widget=forms.TextInput(attrs={
                class: form-control,
            placeholder: Ingresa tu nombre,
            id: id_nombre
        })
    )
