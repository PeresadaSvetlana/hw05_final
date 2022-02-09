from django.test import TestCase

from ..models import Group, Post, User

USERNAME = 'auth'
TEXT_GROUP = 'Тестовая группа'
SLUG = 'Тестовый слаг'
DESCRIPTION = 'Тестовое описание'
SYMBOLS_OF_POST = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(USERNAME)
        cls.group = Group.objects.create(
            title=TEXT_GROUP,
            slug=SLUG,
            description=DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT_GROUP,
        )
        cls.field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
            'author': 'Автор',
        }
        cls.field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        expected_object_name = post.text[:SYMBOLS_OF_POST]
        self.assertEqual(expected_object_name, str(post))

        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_title_label(self):
        """verbose_name поля title совпадает с ожидаемым."""
        for field, expected_value in self.field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text поля title совпадает с ожидаемым."""
        for field, expected_value in self.field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value
                )
