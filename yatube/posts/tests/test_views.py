import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

POSTS_COUNT = 57
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # create an non-authorized client
        cls.guest_client = Client()
        # create two authorized clients
        cls.user1 = User.objects.create(username='User1')
        cls.user2 = User.objects.create(username='User2')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user1)
        cls.authorized_client.force_login(cls.user2)
        cls.small_gif_1 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.small_gif_2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_1 = SimpleUploadedFile(
            name='new1.gif',
            content=cls.small_gif_1,
            content_type='image/gif'
        )

        cls.uploaded_2 = SimpleUploadedFile(
            name='new2.gif',
            content=cls.small_gif_2,
            content_type='image/gif'
        )

        # create first group in DB
        cls.group1 = Group.objects.create(
            title='Title for group1',
            slug='test-slug-1',
            description='Description for group1'
        )
        # create second group in DB
        cls.group2 = Group.objects.create(
            title='Title for group2',
            slug='test-slug-2',
            description='Description for group2'
        )

        cls.post = Post.objects.create(
            text='Test text for user1 group1',
            author=cls.user1,
            group=cls.group1,
            image=cls.uploaded_1,
        )

        cls.post = Post.objects.create(
            text='Test text for user2 group2',
            author=cls.user2,
            group=cls.group2,
            image=cls.uploaded_2,
        )

        cls.index_page = 'posts:index'
        cls.group_list_page = 'posts:group_list'
        cls.profile_page = 'posts:profile'
        cls.post_detail_page = 'posts:post_detail'
        cls.post_create_page = 'posts:post_create'
        cls.post_edit_page = 'posts:post_edit'

        cls.templates_pages_names = {
            reverse(cls.index_page): 'posts/index.html',
            reverse(cls.group_list_page, kwargs={'slug': cls.group1.slug}): (
                'posts/group_list.html'),
            reverse(cls.profile_page, kwargs={'username': cls.user2}): (
                'posts/profile.html'),
            reverse(cls.post_detail_page, kwargs={'post_id': cls.post.id}): (
                'posts/post_detail.html'),
            reverse(cls.post_create_page): 'posts/create.html',
            reverse(cls.post_edit_page, kwargs={'post_id': cls.post.id}): (
                'posts/create.html'),
        }

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    # checking templates and reverse names
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # checking the dictionary of the index page context
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context)
        self.assertEqual(post_object.image, self.post.image)

    # checking context of group_list
    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.group_list_page, kwargs={'slug': self.group2.slug})
        )
        post_object = response.context['page_obj'][0]
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group2)
        self.assertIn('page_obj', response.context)
        self.assertEqual(post_object.image, self.post.image)

    # checking context of profile template
    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.profile_page, kwargs={'username': self.user2})
        )
        post_object = response.context['page_obj'][0]
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user2)
        self.assertIn('posts_count', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['author'], self.user2)
        self.assertEqual(post_object.image, self.post.image)

    # post_detail template is formed with the correct context
    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                self.post_detail_page,
                kwargs={'post_id': (self.post.pk)})).context.get('post')
        self.assertEqual(response.group, self.post.group)
        self.assertEqual(response.text, self.post.text)
        self.assertEqual(response.author, self.post.author)
        self.assertEqual(response.image, self.post.image)

    # template is formed with the correct context
    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # test context of post_edit
    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            self.post_edit_page, args=(self.post.pk,)))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache(self):
        """Тестируем кэш"""
        post = Post.objects.create(
            text='Testing text',
            author=self.user1,
            group=self.group1
        )
        response_1 = self.authorized_client.get(reverse(self.index_page))
        response_before_del = response_1.context['page_obj'][0]
        self.assertEqual(post, response_before_del)
        post.delete()
        response_2 = self.authorized_client.get(reverse(self.index_page))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse(self.index_page))
        self.assertNotEqual(response_1.content, response_3.content)


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if POSTS_COUNT <= 10:
            raise NotImplementedError('Need more than 10 posts')
        else:
            cls.amount_of_post_last_page = (POSTS_COUNT
                                            % settings.POSTS_PER_PAGE)
            cls.amount_of_pages = POSTS_COUNT // settings.POSTS_PER_PAGE

        # create user
        cls.user = User.objects.create(username='user')

        # create group for paginator
        cls.group = Group.objects.create(
            title='Test title',
            slug='test-slug',
            description='Test description',
        )

        # create authorized client
        cls.authorized_client = Client()

        # pages for test
        cls.pages = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': cls.user}),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
        ]

        # create posts
        Post.objects.bulk_create(Post(
            text=f'Test post number {post}',
            author=cls.user,
            group=cls.group,) for post in range(POSTS_COUNT))

    def setUp(self):
        cache.clear()

    # сhecking the number of paginator posts is 10
    def test_paginator_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_PER_PAGE)

    # checking the number of posts of the user on profile page (10)
    def test_paginator_profile_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_PER_PAGE)

    # checking context in pages list
    def test_paginator_on_pages(self):
        '''Проверка работы паджинатора на страницах в списке pages'''
        for page in self.pages:
            with self.subTest(page=page):
                response_obj = self.authorized_client.get(page)
                self.assertEqual(len(response_obj.context['page_obj']),
                                 settings.POSTS_PER_PAGE)
                response_obj2 = self.authorized_client.get(
                    page + f'?page={self.amount_of_pages + 1}')
                self.assertEqual(len(response_obj2.context['page_obj']),
                                 self.amount_of_post_last_page)


class FollowingTest(TestCase):
    """Тест подписок на автора поста"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='User1')
        cls.user2 = User.objects.create_user(username='User2')
        cls.user3 = User.objects.create_user(username='User3')
        cls.authorized_user1 = Client()
        cls.authorized_user1.force_login(cls.user1)
        cls.authorized_user2 = Client()
        cls.authorized_user2.force_login(cls.user2)

    def test_authorized_user_can_follow(self):
        """Авторизированный пользователь имеет
        возможность подписаться на автора поста."""
        page = reverse('posts:profile_follow',
                       kwargs={'username': self.user3})
        self.authorized_user1.get(page)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user1,
                author=self.user3).exists()
        )

    def test_authorized_user_can_unfollow(self):
        """Авторизированный пользователь может отписываться пользователей."""
        Follow.objects.create(user=self.user2, author=self.user3)
        page = reverse('posts:profile_unfollow',
                       kwargs={'username': self.user3})
        self.authorized_user2.get(page)
        self.assertFalse(
            Follow.objects.filter(user=self.user2, author=self.user3).exists())

    def test_new_post_appears_only_subscriber(self):
        """Новая запись появляется у подписавшихся"""
        Follow.objects.create(user=self.user1, author=self.user3)
        post = Post.objects.create(author=self.user3, text='Test text')
        page = reverse('posts:follow_index')
        response_obj_1 = self.authorized_user1.get(page)
        response_obj_2 = self.authorized_user2.get(page)
        test_post1 = response_obj_1.context['page_obj']
        test_post2 = response_obj_2.context['page_obj']
        self.assertIn(post, test_post1)
        self.assertNotIn(post, test_post2)
