from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from .validators import validate_listing_title
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import re

class User(AbstractUser):
    # additional fields
    phone_number = models.CharField(max_length=12, blank=True)    
    # required fields
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name



class Listing(models.Model):
    title = models.CharField(max_length=64, unique=True, validators=[validate_listing_title])
    description = models.CharField(max_length=512)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)  # Initial price
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Highest bid
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    watchlist = models.ManyToManyField(User, blank=True, related_name="watchlisted_items")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings_owned")
    bidders = models.ManyToManyField(User, through='Bid', related_name='bids', blank=True)  # Changed to plural
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="listings_won", null=True, blank=True)  # Changed to SET_NULL
    created_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)  # Optional: auction end time
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Set current_price to starting_price if not set
        if not self.current_price:
            self.current_price = self.starting_price
        super().save(*args, **kwargs)
        
    def get_current_price_safe(self):
        """Safe method to get current price, handling None case"""
        return self.current_price if self.current_price is not None else self.starting_price
    
    # Then in your Bid model, you can use:
    # current_price = self.listing.get_current_price_safe()
    
    def get_current_price(self):
        """Returns the current price (highest bid or starting price)"""
        return self.current_price or self.starting_price
    
    def get_highest_bid(self):
        """Returns the highest bid object"""
        return self.bid_set.order_by('-amount').first()
    
    def get_bid_count(self):
        """Returns total number of bids"""
        return self.bid_set.count()
    
    def is_auction_active(self):
        """Check if auction is still active"""
        if self.end_date:
            return self.is_active and timezone.now() < self.end_date
        return self.is_active
    
    def can_user_bid(self, user):
        """Check if user can place a bid"""
        if not user.is_authenticated:
            return False, "You must be logged in to bid."
        if user == self.owner:
            return False, "You cannot bid on your own listing."
        if not self.is_auction_active():
            return False, "This auction is no longer active."
        return True, ""
    
    def close_auction(self):
        """Close the auction and set the winner"""
        highest_bid = self.get_highest_bid()
        if highest_bid:
            self.winner = highest_bid.user
            self.is_active = False
            self.save()
            return self.winner
        return None
    
class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-amount']
    
    def clean(self):
        """Fixed validation to handle None values properly"""
        if self.amount <= 0:
            raise ValidationError("Bid amount must be greater than 0.")
        
        # Get current price safely
        current_price = self.listing.current_price
        if current_price is None:
            current_price = self.listing.starting_price
        
        # Basic price comparison
        if self.amount <= current_price:
            raise ValidationError(
                f"Bid must be higher than the current price of ${current_price:.2f}."
            )
        
        # ADD THE MINIMUM INCREMENT CHECK HERE - Change 1.00 to 3.00
        min_increment = Decimal('3.00')  # ← CHANGE THIS NUMBER TO 3.00
        if self.amount < current_price + min_increment:
            raise ValidationError(
                f"Bid must be at least ${min_increment:.2f} higher than the current price of ${current_price:.2f}."
            )
        
        if self.user == self.listing.owner:
            raise ValidationError("You cannot bid on your own listing.")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # This calls the fixed clean() method
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"${self.amount} by {self.user.username} on {self.listing.title}"