from django import forms
from .models import CartItem


class AddToCartForm(forms.Form):
    size_id = forms.IntegerField(required=False)
    quantity = forms.IntegerField(min_value=1, initial=1)


    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

        if product:
            # Включаем ВСЕ размеры в choices, а проверку остатка делаем в view
            all_sizes = product.product_sizes.all()
            if all_sizes.exists():
                self.fields['size_id'] = forms.ChoiceField(
                    choices=[(ps.id, ps.size.name) for ps in all_sizes],
                    required=False,
                    initial=all_sizes.filter(stock__gt=0).first().id if all_sizes.filter(stock__gt=0).exists() else None
                )
            else:
                # Если нет размеров, удаляем поле size_id совсем или делаем его полностью опциональным
                self.fields['size_id'] = forms.CharField(required=False)
                print(f"DEBUG: Product {product.name} has no sizes, made size_id optional CharField")
    

class UpdateCartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.product_size:
            self.fields['quantity'].validators.append(
                forms.validators.MaxValueValidator(self.instance.product_size.stock)
            )