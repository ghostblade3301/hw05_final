import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # create a non-authorized
        cls.guest_client = Client()
        # create an authorized client
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # create test image
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='new.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        # create group in DB
        cls.group = Group.objects.create(
            title='Title for post',
            slug='test-slug',
            description='Description for group'
        )

        # create post in DB
        cls.post = Post.objects.create(
            text='Text for post',
            author=cls.user,
            group=cls.group,
        )

        cls.profile_page = 'posts:profile'
        cls.post_detail_page = 'posts:post_detail'
        cls.post_create_page = 'posts:post_create'
        cls.post_edit_page = 'posts:post_edit'

    @classmethod
    def tearDownClass(cls):
        """Удаляет тестовые картинки после теста."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_authorized(self):
        """При отправке валидной формы создается запись"""
        # amount of posts
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Text for post',
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse(self.post_create_page),
            data=form_data,
            follow=True
        )
        # checking redirect
        self.assertRedirects(response, reverse(
            self.profile_page, kwargs={'username': self.user})
        )
        # checking amount of posts
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # checking existence of the new post
        last_post = Post.objects.first()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.group_id, form_data['group'])
        self.assertEqual(self.uploaded, form_data['image'])

    def test_create_post_guest(self):
        """Неавторизованный не может создать пост"""
        # non-authorized client can't create a post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Post from non-authorized client',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse(self.post_create_page),
            data=form_data,
            follow=True,
        )
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_authorized(self):
        """Пост может редактировать создатель"""
        # authorized client can modify his post
        form_data = {
            'text': 'Edited post',
            'group': self.group.pk
        }
        response_edit = self.authorized_client.post(
            reverse(self.post_edit_page, args=[self.post.id]),
            data=form_data,
            follow=True,)
        self.assertRedirects(
            response_edit,
            reverse(self.post_detail_page, kwargs={'post_id': self.post.id})
        )

        post_edit = Post.objects.get(pk=self.group.pk)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, form_data['text'])
        self.assertEqual(post_edit.author, self.user)
        self.assertEqual(post_edit.group_id, form_data['group'])


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # create group in DB
        cls.group = Group.objects.create(
            title='Title for post',
            slug='test-slug',
            description='Description for group'
        )

        # create post in DB
        cls.post = Post.objects.create(
            text='Text for post',
            author=cls.user,
            group=cls.group,
        )

    def test_comment_form(self):
        """Проверка создания комментария с дальнейшим редиректом"""
        form_data = {
            'text': 'Test comment',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comment = Comment.objects.get(text=form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post.id, self.post.id)
