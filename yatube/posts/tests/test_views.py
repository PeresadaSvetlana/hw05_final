import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

USERNAME = 'user_author'
ANOTHER_USERNAME = 'another_user'
GROUP_NAME = 'Наименование группы'
SLUG = 'text-slug'
DESCRIPTION = 'Текстовое описание'
TEXT_HEADER = 'Тестовый заголовок'
NEW_GROUP = 'Новая группа'
NEW_SLUG = 'new-slug'
NEW_DESCRIPTION = 'Описание новой группы'
NEW_HEADER = 'Новый заголовок'
NUMBER_OF_POSTS_ALL = 13
NUMBER_OF_POSTS_PAGE = 10
NUMBER_OF_POSTS_REMAINDER = 3
CACHE_TEXT = 'Для проверки кеша'
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user_author = User.objects.create_user(USERNAME)
        cls.another_user = User.objects.create_user(ANOTHER_USERNAME)
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title=GROUP_NAME,
            slug=SLUG,
            description=DESCRIPTION
        )
        cls.post = Post.objects.create(
            text=TEXT_HEADER,
            author=cls.user_author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={
                'slug': cls.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': cls.user_author.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': cls.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': cls.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        cls.comment_form = {
            'text': forms.fields.CharField,
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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
        # Очищаем кэш
        cache.clear()

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_page_show_correct_context(self):
        """Шаблон posts:index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post_index = response.context['page_obj'][0]
        post_text = post_index.text
        post_author = post_index.author
        post_group = post_index.group
        post_image = post_index.image
        self.assertEqual(post_text, TEXT_HEADER)
        self.assertEqual(post_author, self.user_author)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_image, self.post.image)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        group_title = group.title
        group_slug = group.slug
        group_description = group.description
        self.assertEqual(group_title, GROUP_NAME)
        self.assertEqual(group_slug, SLUG)
        self.assertEqual(group_description, DESCRIPTION)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_author.username})
        )
        post = response.context['page_obj'][0]
        post_text = post.text
        post_author = post.author
        post_group = post.group
        post_image = post.image
        self.assertEqual(post_text, TEXT_HEADER)
        self.assertEqual(post_author, self.user_author)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_image, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

        post = response.context['post']
        post_text = post.text
        post_author = post.author
        post_group = post.group
        post_image = post.image
        self.assertEqual(post_text, TEXT_HEADER)
        self.assertEqual(post_author, self.user_author)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_image, self.post.image)
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in self.comment_form.items():
            with self.subTest(value=value):
                comment_form = response.context.get(
                    'comment_form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(comment_form, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        # Проверяем, что типы полей формы в
        # словаре context соответствуют ожиданиям
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_group_test(self):
        """
        Проверяем, что при создании поста
        с указанием группы пост появляется на нужных страницах.
        """
        Group.objects.create(
            title=NEW_GROUP,
            slug=NEW_SLUG,
            description=NEW_DESCRIPTION
        )
        Post.objects.create(
            text=NEW_HEADER,
            author=self.user_author,
            group=self.group
        )
        """Пост появился на главной странице """
        response_1 = self.guest_client.get(reverse('posts:index'))
        post_new = response_1.context['page_obj'][0]
        self.assertEqual(post_new.text, NEW_HEADER)
        """Пост появился в нужной группе """
        response_2 = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': NEW_SLUG})
        )
        group = response_2.context['group']
        group_title = group.title
        group_slug = group.slug
        group_description = group.description
        self.assertEqual(group_title, NEW_GROUP)
        self.assertEqual(group_slug, NEW_SLUG)
        self.assertEqual(group_description, NEW_DESCRIPTION)
        """Пост отобразился в профайле пользователя"""
        response_3 = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_author.username})
        )
        post = response_3.context['page_obj'][0]
        post_text = post.text
        self.assertEqual(post_text, NEW_HEADER)


class CacheViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
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
        for num_page in range(NUMBER_OF_POSTS_ALL):
            cls.post = Post.objects.create(
                text=f'Тестовый заголовок{num_page} ',
                author=cls.user_author,
                group=cls.group
            )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_cache_post_index(self):
        cache_post = Post.objects.create(
            text=CACHE_TEXT,
            author=self.user_author,
            group=self.group
        )
        response_one = self.guest_client.get(reverse('posts:index'))
        post_content = response_one.content
        cache_post.delete()
        responce_two = self.guest_client.get(reverse('posts:index'))
        post_content_two = responce_two.content
        self.assertEqual(post_content, post_content_two)
        cache.clear()
        response_one = self.guest_client.get(reverse('posts:index'))
        post_content_three = response_one.content
        self.assertNotEquals(post_content, post_content_three)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
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
        for num_page in range(NUMBER_OF_POSTS_ALL):
            cls.post = Post.objects.create(
                text=f'Тестовый заголовок{num_page} ',
                author=cls.user_author,
                group=cls.group
            )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(
            len(response.context['page_obj']), NUMBER_OF_POSTS_PAGE
        )

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.guest_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), NUMBER_OF_POSTS_REMAINDER
        )


class FollowViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
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
        for num_page in range(NUMBER_OF_POSTS_ALL):
            cls.post = Post.objects.create(
                text=f'Тестовый заголовок{num_page} ',
                author=cls.user_author,
                group=cls.group
            )

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
        # Очищаем кэш
        cache.clear()

    def test_authorized_client_follow(self):
        user = self.another_user
        author = self.user_author
        count = Follow.objects.count()
        Follow.objects.create(user=user, author=author)
        cache.clear()
        self.assertNotEquals(Follow.objects.count(), count)

    def test_authorized_client_unfollow(self):
        user = self.another_user
        author = self.user_author
        count = Follow.objects.count()
        Follow.objects.filter(user=user, author=author).delete()
        cache.clear()
        self.assertEquals(Follow.objects.count(), count)

    def test_unfollow_user(self):
        user = self.another_user
        author = self.user_author
        Follow.objects.create(user=user, author=author)
        count_one = len(Post.objects.filter(author__following__user=user))
        Post.objects.create(
            text=NEW_HEADER,
            author=self.another_user,
            group=self.group
        )
        cache.clear()
        count_two = len(Post.objects.filter(author__following__user=user))
        self.assertEquals(count_one, count_two)

    def test_follow_user(self):
        user = self.another_user
        author = self.user_author
        Follow.objects.create(user=user, author=author)
        count_one = len(Post.objects.filter(author__following__user=user))
        Post.objects.create(
            text=NEW_HEADER,
            author=self.user_author,
            group=self.group
        )
        cache.clear()
        count_two = len(Post.objects.filter(author__following__user=user))
        self.assertNotEquals(count_one, count_two)
