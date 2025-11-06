from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            return redirect('users:login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main:index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    return render(request, 'users/login.html')

@login_required
def profile_view(request):
    """Профиль пользователя"""
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def account_details(request):
    """Детали аккаунта"""
    return render(request, 'users/account_details.html', {'user': request.user})

@login_required
def edit_account_details(request):
    """Редактирование деталей аккаунта"""
    return render(request, 'users/edit_account_details.html', {'user': request.user})

@login_required
def update_account_details(request):
    """Обновление деталей аккаунта"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Данные аккаунта обновлены!')
        return redirect('users:account_details')
    return redirect('users:edit_account_details')

def logout(request):
    """Выход пользователя"""
    auth_logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('main:index')

@login_required
def order_history(request):
    """История заказов"""
    # Здесь будет логика для получения заказов пользователя
    orders = []  # Пока что пустой список
    return render(request, 'users/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Детали конкретного заказа"""
    # Здесь будет логика для получения конкретного заказа
    order = None  # Пока что None
    return render(request, 'users/order_detail.html', {'order': order, 'order_id': order_id})
