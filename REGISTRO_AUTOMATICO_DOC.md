# Sistema de Registro Automático - Documentación

## 🎉 ¿Qué se implementó?

Se creó un **sistema de registro completamente automático** donde los nuevos usuarios pueden:

1. **Crear una cuenta** llenando un formulario 
2. **Guardar automáticamente** en la base de datos:
   - Un usuario Django (`User`)
   - Un cliente (`Cliente`)
   - Un carrito vacío (`Carrito`)
3. **Iniciar sesión automáticamente** después del registro
4. **Acceder al catálogo** inmediatamente

---

## 📁 Archivos Nuevos/Modificados

### **NUEVOS:**

| Archivo | Descripción |
|---------|-------------|
| [tienda/forms.py](tienda/forms.py) | Formulario `SignUpForm` que crea User + Cliente + Carrito |
| [tienda/templates/signup.html](tienda/templates/signup.html) | Página de registro (diseño consistente con login) |

### **MODIFICADOS:**

| Archivo | Cambio |
|---------|--------|
| [tienda/views.py](tienda/views.py) | Agregada `SignUpView` para manejar el registro |
| [tienda/urls.py](tienda/urls.py) | Agregada ruta `/signup/` |
| [tienda/templates/login.html](tienda/templates/login.html) | Link "Crea una aquí" apunta a signup |

---

## 🔄 Flujo de Registro

```
Usuario → Accede a /signup/ → Llena formulario → ✓ Valida
           ↓
      Se crea automáticamente:
      - User (Django auth)
      - Cliente (modelo personalizado)
      - Carrito (vacío, listo para comprar)
      ↓
      Usuario se loguea automáticamente
      ↓
      Redirige a /catalogo/
```

---

## 📋 Campo del Formulario

El formulario de registro pide:

| Campo | Tipo | Requerido | Validación |
|-------|------|-----------|-----------|
| **Nombre Completo** | Texto | ✓ Sí | Max 100 caracteres |
| **Email** | Email | ✓ Sí | Único (no duplicado en User ni Cliente) |
| **Dirección** | Texto | ✓ Sí | Max 255 caracteres |
| **Teléfono** | Texto | ✓ Sí | Max 20 caracteres (formato flexible) |
| **Contraseña** | Password | ✓ Sí | Django security (min 8 chars, no solo números) |
| **Confirmar Contraseña** | Password | ✓ Sí | Debe coincidir |

---

## 🛡️ Seguridad

✅ **Implementadas:**
- Validación de emails únicos (no duplicar en User ni Cliente)
- Validación de contraseñas usando `UserCreationForm` de Django
- Los campos contraseña nunca se envían en radio o se exponen
- CSRF token en todos los formularios
- Hashing de contraseñas automático por Django

---

## 📝 Ejemplo de Uso

### **Cliente intenta registrarse:**

1. Va a `http://localhost:8000/signup/`
2. Completa:
   - Nombre: "Juan García"
   - Email: "juan@example.com"
   - Dirección: "Calle 5 #123, Bogotá"
   - Teléfono: "+57 300 1234567"
   - Password: "MiContraseña123!"
3. Presiona "Crear Cuenta"
4. **Automáticamente se crean:**
   ```python
   # En la base de datos:
   User.objects.create(
       username="juan@example.com",
       email="juan@example.com",
       first_name="Juan García"
   )
   
   Cliente.objects.create(
       nombre="Juan García",
       email="juan@example.com",
       direccion="Calle 5 #123, Bogotá",
       telefono="+57 300 1234567"
   )
   
   Carrito.objects.create(
       cliente=cliente_creado
   )
   ```
5. Usuario se loguea automáticamente
6. Se redirige a `/catalogo/`

---

## 🔗 URLs Relacionadas

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/signup/` | `SignUpView` | Página de registro |
| `/login/` | `LoginView` | Página de login |
| `/logout/` | `logout_view` | Cerrar sesión |
| `/catalogo/` | `CatalogoView` | Catálogo de productos (después del registro) |

---

## ⚙️ Cómo Funciona el Formulario Internamente

### **1. Validación de Email Único:**
```python
def clean_email(self):
    email = self.cleaned_data.get('email')
    
    # Verificar que no exista en User
    if User.objects.filter(email=email).exists():
        raise forms.ValidationError("Este email ya está registrado en usuario.")
    
    # Verificar que no exista en Cliente
    if Cliente.objects.filter(email=email).exists():
        raise forms.ValidationError("Este email ya está registrado como cliente.")
    
    return email
```

### **2. Creación Automática:**
```python
def save(self, commit=True):
    user = super().save(commit=False)
    user.username = self.cleaned_data['email']  # Email como username
    
    if commit:
        user.save()  # Guardar User
        
        # Crear Cliente automáticamente
        cliente = Cliente.objects.create(
            nombre=self.cleaned_data['first_name'],
            email=self.cleaned_data['email'],
            direccion=self.cleaned_data['direccion'],
            telefono=self.cleaned_data['telefono']
        )
        
        # Crear Carrito automáticamente
        Carrito.objects.create(cliente=cliente)
    
    return user
```

### **3. Login Automático:**
```python
def form_valid(self, form):
    user = form.save()
    login(self.request, user)  # ← Auto-login
    return redirect(self.success_url)
```

---

## 🚀 Próximos Pasos (Opcionales)

Si quieres mejorar más el sistema de registro:

1. **Verificación de Email:**
   - Enviar email de confirmación
   - Link para activar cuenta
   - Transacciones atómicas para rollback

2. **Validación Mejorada:**
   - Verificar formato de teléfono
   - Usar librería de validación de email
   - Captcha para prevenir bots

3. **Mensaje de Bienvenida:**
   - Email de bienvenida automático
   - Cupón de descuento "bienvenida"
   - Mensajes flash después del registro

4. **Social Login:**
   - Registro con Google
   - Registro con Facebook
   - OAuth integrado

---

## ✅ Checklist de Testing

- [x] Formulario valida datos correctos
- [x] Rechaza emails duplicados
- [x] Rechaza contraseñas que no coinciden
- [x] Crea User automáticamente
- [x] Crea Cliente automáticamente
- [x] Crea Carrito automáticamente
- [x] Usuario se loguea automáticamente
- [x] Redirige al catálogo tras registro
- [x] Template es visualmente consistente
- [x] Link en login apunta a signup

---

## 🔧 Troubleshooting

### **"Este email ya está registrado"**
- Email está en User o Cliente
- Usar otro email o contactar admin

### **"Las contraseñas no coinciden"**
- Reescribir ambas exactamente igual
- Asegurarse de mayúsculas/minúsculas

### **"Contraseña demasiado corta / similar a username"**
- Django requiere mínimo ~8 caracteres
- No puede ser solo números
- No puede ser igual al email

### **Usuario no se loguea automáticamente**
- Verificar que `login()` se ejecutó
- Verificar settings de sesión en `settings.py`

---

**Última actualización:** 26/03/2026  
**Estado:** ✅ Implementado y testeado
