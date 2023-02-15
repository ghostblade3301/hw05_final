from django.test import TestCase

from posts.models import Group, Post, User


class TestPostModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth', )
        cls.group = Group.objects.create(
            title='Test title',
            slug='slug-test',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test post',
        )

    def test_models_have_correct_object_names(self):
        """Проверка корректности работы __str__."""
        group = self.group
        post = self.post
        self.assertEqual(str(self.post), post.text[:15])
        self.assertEqual(str(self.group), group.title)
