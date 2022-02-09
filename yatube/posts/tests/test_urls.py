from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

USERNAME = 'user_author'
ANOTHER_USERNAME = 'another_user'
GROUP_NAME = 'Наименование группы'
SLUG = 'text-slug'
DESCRIPTION = 'Текстовое описание'
TEXT_HEADER = 'Тестовый заголовок'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user_author = User.objects.create_user(USERNAME)
        cls.another_user = User.objects.create_user(ANOTHER_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_NAME,
            slug=SLUG,
            description=DESCRIPTION
        )
        cls.post = Post.objects.create(
            text=TEXT_HEADER,
            author=cls.user_author,
            group=cls.group
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user_author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.public_urls = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.user_author}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
        }
        cls.private_urls = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.user_author}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
        }

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Создаем трейтий клиент
        self.author_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.another_user)
        # Автор поста
        self.author_client.force_login(self.user_author)

    # Проверяем общедоступные страницы
    def test_guest_client(self):
        """Страницы доступна любому пользователю."""
        for url, status in self.public_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_authorized_and_author_client(self):
        """Страницы доступна автору и авторизованному пользователю."""
        for url, status in self.private_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, status)

    # Проверяем редиректы для неавторизованного пользователя
    def test_post_create_url_redirect_anonymous_on_login(self):
        """
        Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, f'{reverse("users:login")}?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """
        Страница /posts/{self.post_id}/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next=/posts/{self.post.id}/edit/"
        )

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернет ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        for url, template in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
