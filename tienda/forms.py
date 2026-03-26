from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Cliente


class SignUpForm(UserCreationForm):
    """Formulario de registro que crea User y Cliente automáticamente"""
    
    # Campos de Django User
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo'
        })
    )
    
    # Campos del Cliente
    direccion = forms.CharField(
        max_length=255,
        required=True,
        label='Dirección',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Calle, número, ciudad'
        })
    )
    telefono = forms.CharField(
        max_length=20,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(+57) 123 456 7890'
        })
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña segura'
        })
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2', 'direccion', 'telefono')
    
    def clean_email(self):
        """Verifica que el email no esté duplicado en User ni en Cliente"""
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado en usuario.")
        
        if Cliente.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado como cliente.")
        
        return email
    
    def clean_password2(self):
        """Verifica que las contraseñas coincidan"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
        return password2
    
    def save(self, commit=True):
        """
        Guarda el User y crea un Cliente automáticamente.
        Retorna el usuario creado.
        """
        user = super().save(commit=False)
        
        # Usar el email como username si no está configurado
        if not user.username:
            user.username = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Crear Cliente automáticamente
            cliente = Cliente.objects.create(
                nombre=self.cleaned_data['first_name'],
                email=self.cleaned_data['email'],
                direccion=self.cleaned_data['direccion'],
                telefono=self.cleaned_data['telefono']
            )
            
            # Crear Carrito automáticamente para el cliente
            from .models import Carrito
            Carrito.objects.create(cliente=cliente)
        
        return user


class PerfilUsuarioForm(forms.ModelForm):
    """Formulario para editar el perfil del usuario (datos de User)"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=False,
        label='Apellido',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu apellido (opcional)'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PerfilClienteForm(forms.ModelForm):
    """Formulario para editar el perfil del cliente (datos de Cliente)"""
    
    direccion = forms.CharField(
        max_length=500,
        required=True,
        label='Dirección de Envío',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Calle, número, ciudad, código postal'
        })
    )
    telefono = forms.CharField(
        max_length=20,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(+57) 123 456 7890'
        })
    )
    
    class Meta:
        model = Cliente
        fields = ['direccion', 'telefono']

