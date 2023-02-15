# core/views.py
from django.shortcuts import render


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failed(request, exception):
    return render(request, 'core/403csrf.html', status=403)


def permission_denied(request, exception):
    return render(request, 'core/403.html', status=403)
