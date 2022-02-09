from http import HTTPStatus
from django.test import TestCase, Client


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем экземпляр клиента
        cls.guest_client = Client()
        cls.templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        cls.templates_url_status = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK
        }

    def test_about(self):
        # Делаем запрос к главной странице и проверяем статус
        for url, status in self.templates_url_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_url_coorect_template(self):
        for url, template in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
