from django.core.mail import send_mail
from .models import CustomUser
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserEmailSerializer, ConfirmationCodeSerializer, UserSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from django.db.models import Avg
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from .models import CustomUser, Title, Review, Comment, Category, Genre
import jwt
from rest_framework import filters, mixins, viewsets, serializers, status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase

from .filters import TitleFilter
from .serializers import (
  CategorySerializer, ConfirmationCodeSerializer,
  GenreSerializer, TitleReadSerializer,
  TitleWriteSerializer, UserEmailSerializer,
  ReviewSerializer, CommentSerializer
)
from rest_framework import generics
from .permissions import (
    IsAdminOrReadOnly,
    IsAdminOrSuperUser,
    ReviewCommentPermissions
)
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAdminUser)




@api_view(['POST'])
@permission_classes([AllowAny])
def get_confirmation_code(request):
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
        [email, ],
        fail_silently=False
    )
    if mail_status:
        return HttpResponse('Код подтверждения был отправлен.')
    user.delete()
    return HttpResponse('Ошибка при отправлении письма')


@api_view(['POST'])
@permission_classes([AllowAny])
def get_jwt_token(request):
    serializer = ConfirmationCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    confirmation_code = request.POST.get('confirmation_code')
    email = request.POST.get('email')
    if email is None:
        return HttpResponse("Введите email")
    if confirmation_code is None:
        return HttpResponse("Введите confirmation_code")
    user = get_object_or_404(CustomUser, email=email)
    token_check = default_token_generator.check_token(user, confirmation_code)
    if token_check is True:
        refresh = RefreshToken.for_user(user)
        return HttpResponse(f'Ваш токен:{refresh.access_token}')
    return HttpResponse('Неправильный confirmation_code')



class UserViewSet(viewsets.ModelViewSet):
    """API для модели пользователя"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAdminOrSuperUser]
    lookup_field = 'username'

    @action(detail=False, methods=['get', 'patch'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """API для получения и редактирования
        текущим пользователем своих данных"""
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=user.role, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CreateDestroyListRetrieveViewSet(mixins.CreateModelMixin,
                                       mixins.ListModelMixin,
                                       mixins.DestroyModelMixin,
                                       viewsets.GenericViewSet):
    pass


class TitleViewSet(ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg('review__score'))
    filterset_class = TitleFilter
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class GenreViewSet(CreateDestroyListRetrieveViewSet):
    queryset = Genre.objects.all()
    lookup_field = 'slug'
    serializer_class = GenreSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class CategoryViewSet(CreateDestroyListRetrieveViewSet):
    queryset = Category.objects.all()
    lookup_field = 'slug'
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [ReviewCommentPermissions,
        IsAuthenticatedOrReadOnly,
    ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        reviews = Review.objects.filter(title=title)
        return reviews

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))

        reviews = self.request.user.reviews
        if reviews.filter(title=title).exists():
            raise serializers.ValidationError(
                detail="Вы уже делали ревью на это произведение!",
                code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [ReviewCommentPermissions, IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        return Comment.objects.filter(review=review)
