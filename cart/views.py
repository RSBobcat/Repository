from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.db import transaction
from main.models import Product, ProductSize
from .models import Cart, CartItem
from .forms import AddToCartForm
import json


class CartMixin:
    def get_cart(self, request):
        if hasattr(request, 'cart'):
            return request.cart
    
        if not request.session.session_key:
            request.session.create()

        # Try to get existing cart first
        cart_id = request.session.get('cart_id')
        cart = None
        
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, session_key=request.session.session_key)
                print(f"DEBUG: Found existing cart {cart.id}")
            except Cart.DoesNotExist:
                print(f"DEBUG: Cart {cart_id} not found, creating new one")
                pass

        if not cart:
            cart, created = Cart.objects.get_or_create(
                session_key=request.session.session_key
            )
            print(f"DEBUG: Cart created/found: {cart.id} (created: {created})")
            request.session['cart_id'] = cart.id
            request.session.modified = True

        request.cart = cart
        return cart
    

class CartModalView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
                'product_size__size'
            ).order_by('-added_at')
        }
        return TemplateResponse(request, 'cart/cart_modal.html', context)


class AddToCartView(CartMixin, View):
    @transaction.atomic
    def post(self, request, slug):
        print(f"DEBUG: POST request to add product {slug} to cart")
        print(f"DEBUG: POST data: {request.POST}")
        print(f"DEBUG: Session key: {request.session.session_key}")
        
        cart = self.get_cart(request)
        print(f"DEBUG: Cart ID: {cart.id if cart else 'None'}")
        
        product = get_object_or_404(Product, slug=slug)
        
        # Debug: Check product sizes
        available_sizes = product.product_sizes.filter(stock__gt=0)
        print(f"DEBUG: Product {product.name} has {available_sizes.count()} available sizes")
        for size in available_sizes:
            print(f"  - Size {size.size.name}: {size.stock} in stock, ProductSize ID: {size.id}")

        form = AddToCartForm(request.POST, product=product)
        
        # Debug: Check all product sizes (not just available)
        all_product_sizes = product.product_sizes.all()
        print(f"DEBUG: Product {product.name} has {all_product_sizes.count()} total sizes:")
        for size in all_product_sizes:
            print(f"  - Size {size.size.name}: {size.stock} in stock, ProductSize ID: {size.id}")
        
        # Debug: Check form choices
        if hasattr(form.fields.get('size_id'), 'choices'):
            print(f"DEBUG: Form size_id choices: {form.fields['size_id'].choices}")
        else:
            print(f"DEBUG: size_id field type: {type(form.fields.get('size_id'))}")
            
        # Debug: Check what was actually received
        print(f"DEBUG: Received size_id: {request.POST.get('size_id')}")
        print(f"DEBUG: Received quantity: {request.POST.get('quantity')}")

        if not form.is_valid():
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Form data: {form.data}")
            return JsonResponse({
                'error': 'Invalid form data',
                'errors': form.errors,
                'debug_info': {
                    'post_data': dict(request.POST),
                    'form_data': form.data,
                }
            }, status=400)
        
        size_id = form.cleaned_data.get('size_id')
        
        if size_id:
            product_size = get_object_or_404(
                ProductSize,
                id=size_id,
                product=product
            )
            # Проверяем наличие товара после получения product_size
            if product_size.stock == 0:
                return JsonResponse({
                    'error': f'Размер "{product_size.size.name}" временно отсутствует на складе'
                }, status=400)
        else:
            product_size = product.product_sizes.filter(stock__gt=0).first()
            if not product_size:
                # Check if product has any sizes at all
                all_sizes = product.product_sizes.all()
                if all_sizes.exists():
                    # Product has sizes but no stock
                    # print(f"DEBUG: No stock for product {product.name}")
                    return JsonResponse({
                        'error': f'Товар "{product.name}" временно отсутствует на складе'
                    }, status=400)
                else:
                    # Product has no sizes - check if default ProductSize already exists
                    print(f"DEBUG: Product has no sizes, checking existing ProductSize")
                    existing_product_size = product.product_sizes.first()
                    if existing_product_size:
                        print(f"DEBUG: Using existing ProductSize: {existing_product_size}")
                        product_size = existing_product_size
                    else:
                        # Create a default size and ProductSize for this product
                        print(f"DEBUG: Creating new default size for product")
                        from main.models import Size
                        try:
                            default_size, created = Size.objects.get_or_create(
                                name='Универсальный',
                                defaults={'display_order': 0}
                            )
                            print(f"DEBUG: Default size created/found: {default_size} (created: {created})")
                            product_size = ProductSize.objects.create(
                                product=product,
                                size=default_size,
                                stock=100  # Default stock
                            )
                            print(f"DEBUG: ProductSize created: {product_size}")
                        except Exception as e:
                            print(f"ERROR: Failed to create size/product_size: {e}")
                            return JsonResponse({'error': f'Failed to create size: {str(e)}'}, status=500)
            

        quantity = form.cleaned_data['quantity']
        if product_size.stock < quantity:
            return JsonResponse({
                'error': f'Only {product_size.stock} items available'
            }, status=400)

        existing_item = cart.items.filter(
            product=product,
            product_size=product_size,
        ).first()

        if existing_item:
            total_quantity = existing_item.quantity + quantity
            if total_quantity > product_size.stock:
                return JsonResponse({
                    'error': f"Cannot add {quantity} items. Only {product_size.stock - existing_item.quantity} more available."
                }, status=400)
            
        cart_item = cart.add_product(product, product_size, quantity)

        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-Request'):
            return redirect('cart:cart_modal')
        else:
            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'message': f"{product.name} added to cart",
                'cart_item_id': cart_item.id
            })
        

class UpdateCartItemView(CartMixin, View):
    @transaction.atomic
    def post(self, request, item_id):
        cart = self.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        quantity = int(data.get('quantity', 1))

        if quantity < 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)
        
        if quantity == 0:
            cart_item.delete()
        else:
            if quantity > cart_item.product_size.stock:
                return JsonResponse({
                    'error': f'Only {cart_item.product_size.stock} items available'
                }, status=400)
            
            cart_item.quantity = quantity
            cart_item.save()

        request.session['cart_id'] = cart.id
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'total_items': cart.total_items,
            'message': 'Cart updated'
        })
    

class RemoveCartItemView(CartMixin, View):
    def post(self, request, item_id):
        cart = self.get_cart(request)

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()

            request.session['cart_id'] = cart.id
            request.session.modified = True

            # If it's an HTMX request, return HTML
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'cart/cart_modal.html', {
                    'cart': cart,
                })
            
            # Otherwise return JSON
            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'message': 'Item removed from cart'
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Item not found'}, status=400)
        
    
class CartCountView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        return JsonResponse({
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal)
        })
    

class ClearCartView(CartMixin, View):
    def post(self, request):
        cart = self.get_cart(request)
        cart.clear()

        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'cart/cart_empty.html', {
                'cart': cart
            })
        return JsonResponse({
            'succes': True,
            'message': 'Cart cleared'
        })


class CartSummaryView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
                'product_size__size'
            ).order_by('-added_at')
        }
        return TemplateResponse(request, 'cart/cart_summary.html', context)