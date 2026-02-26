from rest_framework import permissions

class TienePermisoDinamico(permissions.BasePermission):
    def __init__(self, permiso_requerido):
        self.permiso_requerido = permiso_requerido

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # El Superusuario o rol admin siempre pasa
        if request.user.is_superuser or request.user.rol == 'admin':
            return True
        
        # Validar si el string del permiso está en su lista
        return self.permiso_requerido in request.user.permisos