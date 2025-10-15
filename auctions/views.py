from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from .models import Bid, Category, Listing
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import BidForm, CategoryForm, ListingForm
from django.urls import reverse

from .models import User





def create_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect("index")  # Use redirect instead of HttpResponseRedirect
        else:
            messages.error(request, 'Error creating category. Please check the form for errors.')
    else:
        form = CategoryForm()
    
    return render(request, "auctions/create-category.html", {"form": form, "categories": Category.objects.all()})

def create_listings(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            new_listing = form.save(commit=False)
            new_listing.owner = request.user
            new_listing.save()
            messages.success(request, 'Listing created successfully!')
            return redirect("index")  # Use redirect instead of HttpResponseRedirect
        else:
            messages.error(request, 'Error creating listing. Please check the form for errors.')
            return render(request, "auctions/create-listings.html", {"form": form})
           
    else:
        form = ListingForm()
    return render(request, "auctions/create-listings.html", {
        "form": form,
        "categories": Category.objects.all()  # Still pass categories for the template
    })

@require_POST
@login_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Check if the current user is the owner
    if request.user != listing.owner:
        messages.error(request, "You can only delete your own listings.")
        return redirect('listing_detail', listing_id=listing.id)
    
    # Store the title for the success message before deleting
    listing_title = listing.title
    
    # PERMANENTLY DELETE the listing and all related bids
    listing.delete()
    
    messages.success(request, f'Listing "{listing_title}" has been permanently deleted.')
    return redirect('index')  # Redirect to home page after deletion


def category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    listings = Listing.objects.filter(category=category, is_active=True).order_by('-created_date')
    
    paginator = Paginator(listings, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "auctions/category.html", {
        "category": category,
        "page_obj": page_obj
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


# def toggle_watchlist(request, listing_id):
#     listing = Listing.objects.get(id=listing_id)
#     user = request.user
#     if user in listing.watchlist.all():
#         listing.watchlist.remove(user)
#         messages.info(request, f'Removed {listing.title} from your watchlist.')
#     else:
#         listing.watchlist.add(user)
#         messages.success(request, f'Added {listing.title} to your watchlist.')
#     return redirect('index')


def view_watchlist(request):
    user = request.user
    watchlisted_items = user.watchlisted_items.all()
    return render(request, "auctions/watchlist.html", {
        "watchlisted_items": watchlisted_items
    })



def index(request):
    owner = request.user
    all_listings = Listing.objects.all().order_by('-created_date')  # Use appropriate field
    
    paginator = Paginator(all_listings, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "auctions/index.html", {
        'owner': owner, 
        'page_obj': page_obj
    })

@require_POST
@login_required
def toggle_watchlist_ajax(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    
    if request.user in listing.watchlist.all():
        listing.watchlist.remove(request.user)
        is_watchlisted = False
        message = f'Removed "{listing.title}" from your watchlist.'
    else:
        listing.watchlist.add(request.user)
        is_watchlisted = True
        message = f'Added "{listing.title}" to your watchlist.'
    
    return JsonResponse({
        'status': 'success',
        'is_watchlisted': is_watchlisted,
        'message': message,
        'watchlist_count': listing.watchlist.count()
    })
    
    
@login_required
def watchlist_count(request):
    count = request.user.watchlisted_items.count()
    return JsonResponse({
        'count': count
    })
    
    
    
def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    is_watchlisted = request.user in listing.watchlist.all() if request.user.is_authenticated else False
    
    # Get bids for this listing and paginate them
    bids = listing.bid_set.all().order_by('-amount')  # Get all bids for this listing, highest first
    paginator = Paginator(bids, 10)  # 10 bids per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "is_watchlisted": is_watchlisted,
        'page_obj': page_obj,
        'bids': bids  # Also pass the full queryset if needed
    })
    

@login_required
def place_bid(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    if request.method == "POST":
        amount_str = request.POST.get('amount', '').strip()
        
        try:
            amount = Decimal(amount_str)
            
            # Basic validation
            if amount <= 0:
                messages.error(request, "Bid amount must be greater than 0.")
                return redirect('listing_detail', listing_id=listing.id)
            
            if request.user == listing.owner:
                messages.error(request, "You cannot bid on your own listing.")
                return redirect('listing_detail', listing_id=listing.id)
            
            if not listing.is_active:
                messages.error(request, "This auction is no longer active.")
                return redirect('listing_detail', listing_id=listing.id)
            
            # Use the same safe pattern as the model
            current_price = listing.current_price
            if current_price is None:
                current_price = listing.starting_price
            
            if amount <= current_price:
                messages.error(request, f"Bid must be higher than the current price of ${current_price:.2f}.")
                return redirect('listing_detail', listing_id=listing.id)
            
            # Create and validate the bid
            bid = Bid(
                user=request.user,
                listing=listing,
                amount=amount
            )
            
            try:
                bid.full_clean()  # This will use your fixed validation
                bid.save()
                
                # Update listing current price
                listing.current_price = amount
                listing.save()
                
                messages.success(request, f'✅ Bid of ${amount:.2f} placed successfully!')
                
            except ValidationError as e:
                # Handle model validation errors
                for error in e.messages:
                    messages.error(request, error)
            
        except InvalidOperation:
            messages.error(request, "Invalid bid amount. Please enter a valid number.")
        except Exception as e:
            messages.error(request, f"Error placing bid: {str(e)}")
    
    return redirect('listing_detail', listing_id=listing.id)

@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Only owner can close auction
    if request.user != listing.owner:
        messages.error(request, "Only the listing owner can close the auction.")
        return redirect('listing_detail', listing_id=listing.id)
    
    winner = listing.close_auction()
    if winner:
        messages.success(request, f"Auction closed! Winner: {winner.username}")
    else:
        messages.info(request, "Auction closed with no bids.")
    
    return redirect('listing_detail', listing_id=listing.id)