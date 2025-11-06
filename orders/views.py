from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from cart.models import Cart
from .models import Order, OrderItem


class CheckoutView(View):
    """Страница оформления заказа"""
    def get(self, request):
        # Получаем корзину
        if not request.session.session_key:
            request.session.create()
        
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
            cart_items = cart.items.select_related('product', 'product_size__size').all()
            
            if not cart_items:
                messages.warning(request, 'Ваша корзина пуста')
                return redirect('main:index')
                
        except Cart.DoesNotExist:
            messages.warning(request, 'Ваша корзина пуста')
            return redirect('main:index')
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
        }
        return render(request, 'orders/checkout.html', context)


class CreateOrderView(View):
    """Создание заказа"""
    def post(self, request):
        # Получаем корзину
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Корзина пуста'})
        
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
            cart_items = cart.items.all()
            
            if not cart_items.exists():
                return JsonResponse({'success': False, 'message': 'Корзина пуста'})
            
            # Создаем заказ
            order = Order.objects.create(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address1=request.POST.get('address1'),
                city=request.POST.get('city'),
                special_instructions=request.POST.get('special_instructions', ''),
                total_amount=cart.subtotal
            )
            
            # Создаем элементы заказа
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_size=cart_item.product_size,
                    quantity=cart_item.quantity,
                    price=cart_item.product_size.price
                )
            
            # Очищаем корзину
            cart.delete()
            
            return JsonResponse({
                'success': True, 
                'message': 'Заказ успешно оформлен!',
                'redirect_url': f'/orders/success/{order.id}/'
            })
            
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Корзина не найдена'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})


class OrderSuccessView(TemplateView):
    """Страница успешного оформления заказа"""
    template_name = 'orders/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                context['order'] = order
            except Order.DoesNotExist:
                pass
        return context


class OrderHistoryView(View):
    """История заказов пользователя"""
    def get(self, request):
        # Для демонстрации показываем все заказы
        # В реальном приложении нужно фильтровать по пользователю
        orders = Order.objects.all().order_by('-created_at')
        return render(request, 'orders/history.html', {'orders': orders})


class OrderDetailView(View):
    """Детали конкретного заказа"""
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'orders/detail.html', {'order': order})
