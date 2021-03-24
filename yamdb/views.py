from django.shortcuts import render
from django.core.mail import send_mail
from .models import CustomUser
import jwt
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework import filters, mixins, viewsets

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserEmailSerializer, ConfirmationCodeSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)

@api_view(['POST'])
@permission_classes([AllowAny])
def SendMessage(request):
    serializer = UserEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = request.POST.get('email')
    if email is None:
        return HttpResponse("Введите email")
    user = CustomUser.objects.create(email=email)
    confirmation_code = default_token_generator.make_token(user)
    mail_status = send_mail(
        'Код подтверждения:',
        confirmation_code,
        'aintnevertoldnolie@mail.ru',
        [email,],
        fail_silently=False
    )
    if mail_status:
        return HttpResponse('Код подтверждения был отправлен.')
    user.delete()
    return HttpResponse('Ошибка при отправлении письма')

@api_view(['POST'])
@permission_classes([AllowAny])
def SendToken(request):
    serializer = ConfirmationCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    confirmation_code = request.POST.get('confirmation_code')
    email = request.POST.get('email')
    if confirmation_code is None:
        return HttpResponse("Введите confirmation_code")
    if email is None:
        return HttpResponse("Введите email")
    token_check = default_token_generator.check_token(email, confirmation_code)
    if token_check is True:
        user = get_object_or_404(CustomUser, email=email)
        refresh = RefreshToken.for_user(user)
        return HttpResponse(f'Ваш токен:{refresh.access_token}')
    return HttpResponse('Неправильный confirmation_code')
