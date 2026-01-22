from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'), 
    path('dashboard/', crypto_dashboard, name='crypto_dashboard'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("edit-portfolio/<int:portfolio_id>/", edit_portfolio, name="edit_portfolio"),
    path("delete-portfolio/<int:portfolio_id>/", delete_portfolio, name="delete_portfolio"),

]
