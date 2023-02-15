# posts/tests/test_urls.py
from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class TestPostsURLs(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # create non-authorized client
        cls.guest_client = Client()

        # create authorized client
        cls.user = User.objects.create(username='Test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # create group in DB
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )

        # create post in DB
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Text for test',
        )

        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create.html',
            '/nopage/': 'core/404.html',
        }

    # test templates and pages
    def test_urls_uses_correct_template(self):
        cache.clear()
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
