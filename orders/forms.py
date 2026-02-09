from django import forms


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        label='Адрес доставки',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True
    )
    delivery_phone = forms.CharField(label='Телефон для доставки', max_length=20, required=True)
    comment = forms.CharField(
        label='Комментарий к заказу',
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            if user.address:
                self.fields['delivery_address'].initial = user.address
            if user.phone:
                self.fields['delivery_phone'].initial = user.phone
