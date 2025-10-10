from decimal import Decimal
from django import forms
from .models import Listing, Category

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_price', 'image', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter listing title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'starting_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        if len(title) > 200:
            raise forms.ValidationError("Title cannot exceed 200 characters.")
        return title
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) > 512:
            raise forms.ValidationError("Description cannot exceed 512 characters.")
        return description
        
        
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError("Category name must be at least 3 characters long.")
        if len(name) > 64:
            raise forms.ValidationError("Category name cannot exceed 64 characters.")
        return name

class BidForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'step': '0.01', 
            'placeholder': 'Enter your bid amount'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.listing = kwargs.pop('listing', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum value in HTML if listing is provided
        if self.listing:
            min_value = float(self.listing.get_current_price() + Decimal('0.01'))
            self.fields['amount'].widget.attrs['min'] = f"{min_value:.2f}"
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if not self.listing or not self.user:
            return amount  # Basic validation only
        
        # Check basic amount validation
        if amount <= 0:
            raise forms.ValidationError("Bid amount must be greater than 0.")
        
        # Check if user can bid
        can_bid, message = self.listing.can_user_bid(self.user)
        if not can_bid:
            raise forms.ValidationError(message)
        
        # Check if bid is higher than current price
        current_price = self.listing.get_current_price()
        if amount <= current_price:
            raise forms.ValidationError(
                f"Bid must be higher than the current price of ${current_price:.2f}."
            )
        
        # Optional: Check minimum increment
        min_increment = Decimal('1.00')  # $1 minimum increment
        if amount < current_price + min_increment:
            raise forms.ValidationError(
                f"Bid must be at least ${min_increment:.2f} higher than the current price."
            )
        
        return amount