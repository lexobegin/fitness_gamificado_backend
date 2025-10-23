from rest_framework import permissions

class EsAdministrador(permissions.BasePermission):
    """
    Permiso personalizado para verificar que el usuario es administrador
    (acceso al panel Angular)
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and
            request.user.tipo_usuario == 'administrador'
        )


class EsUsuarioFinal(permissions.BasePermission):
    """
    Permiso personalizado para verificar que el usuario es usuario final
    (acceso a la app Flutter)
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and
            request.user.tipo_usuario == 'usuario_final'
        )


class EsSuperUsuario(permissions.BasePermission):
    """
    Permiso para superusuarios (acceso total al backend)
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class PermisoPorTipo(permissions.BasePermission):
    """
    Permiso que permite acceso basado en el tipo de usuario
    """
    def __init__(self, tipos_permitidos):
        self.tipos_permitidos = tipos_permitidos

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and
            request.user.tipo_usuario in self.tipos_permitidos
        )