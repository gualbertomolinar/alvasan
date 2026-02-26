from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Añadimos datos personalizados al token
        token['usuario'] = user.username
        token['rol'] = user.rol
        token['permisos'] = user.permisos
        return token