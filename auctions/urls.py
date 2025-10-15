from django.urls import path

from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create-listings", views.create_listings, name="create-listings"),
    path("create-category", views.create_category, name="create-category"),
    path("category/<int:category_id>", views.category, name="category"),
    path("watchlist", views.view_watchlist, name="watchlist"),
    path("watchlist/toggle/<int:listing_id>", views.toggle_watchlist_ajax, name="toggle_watchlist"),
    path('watchlist/count/', views.watchlist_count, name='watchlist_count'),
    path('listing_detail/<int:listing_id>', views.listing_detail, name='listing_detail'),
    path('listing/<int:listing_id>/bid/', views.place_bid, name='place_bid'),
    path('listing/<int:listing_id>/close/', views.close_auction, name='close_auction'),
    path('listing/<int:listing_id>/delete/', views.delete_listing, name='delete_listing'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)