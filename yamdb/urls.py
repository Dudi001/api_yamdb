from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from .views import SendMessage, SendToken

urlpatterns = [
    path('v1/auth/email/', SendMessage, name='message_sending_view'),
    path('v1/auth/token/', SendToken, name='token_obtain_pair'),
      ]
