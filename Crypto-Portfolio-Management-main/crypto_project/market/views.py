import requests
import json
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Portfolio
from .forms import PortfolioForm, SignupForm  # Ensure both forms are imported
import logging

def home(request):
    return render(request, 'market/home.html')

logger = logging.getLogger(__name__)

@login_required
def crypto_dashboard(request):
    cache_key_market = "crypto_market_data"
    cache_key_historical = "crypto_historical_data"

    # Fetch Market Data (Cached)
    market_data = cache.get(cache_key_market)
    if not market_data:
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 50,  # Fetch top 50 coins
                "page": 1,
                "sparkline": False  # No inline historical data
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            market_data = response.json()
            cache.set(cache_key_market, market_data, timeout=300)  # Cache for 5 min
        except requests.RequestException as e:
            logger.error(f"Error fetching market data: {e}")
            market_data = []

    # Convert Market Data into Dictionary for Quick Lookup
    price_data = {}
    for coin in market_data:
        print(coin)  # Debug each coin
        price_data[coin["id"]] = {
            "price": coin.get("current_price", 0),
            "market_cap": coin.get("market_cap", 0)
        }


    # Fetch Historical Data (Cached)
    historical_data = cache.get(cache_key_historical)
    if not historical_data:
        historical_data = {}
        try:
            for coin in price_data.keys():  # Loop through coins we have prices for
                history_url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
                params = {"vs_currency": "usd", "days": "7", "interval": "daily"}
                history_response = requests.get(history_url, params=params, timeout=10)
                if history_response.status_code == 200:
                    historical_data[coin] = history_response.json().get("prices", [])
            cache.set(cache_key_historical, historical_data, timeout=300)  # Cache for 5 min
        except requests.RequestException as e:
            logger.error(f"Error fetching historical data: {e}")

    # Convert historical data to JSON for frontend
    historical_data_json = json.dumps(historical_data)

    # Fetch User Portfolio
    portfolio = Portfolio.objects.filter(user=request.user).values("id", "coin", "quantity")
    portfolio_items = []
    portfolio_value = 0

    for item in portfolio:
        coin_name = item["coin"].lower()
        current_price = price_data.get(coin_name, {}).get("price", 0)
        current_value = item["quantity"] * current_price
        portfolio_items.append({
            "id": item["id"],
            "coin": item["coin"],
            "quantity": item["quantity"],
            "current_value": current_value,
        })
        portfolio_value += current_value

    # Handle Portfolio Form Submission
    if request.method == "POST":
        form = PortfolioForm(request.POST)
        if form.is_valid():
            portfolio_item = form.save(commit=False)
            portfolio_item.user = request.user
            portfolio_item.save()
            return redirect("crypto_dashboard")
    else:
        form = PortfolioForm()

    return render(request, "market/index.html", {
        "crypto_data": market_data,  # Market data for UI
        "portfolio": portfolio_items,
        "portfolio_value": portfolio_value,
        "form": form,
        "historical_data_json": historical_data_json  # Historical data for charts
    })

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('crypto_dashboard')  # Redirect after signup
    else:
        form = SignupForm()

    return render(request, 'market/signup.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('crypto_dashboard')
    return render(request, 'market/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

# Edit Portfolio
@login_required
def edit_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    if request.method == "POST":
        form = PortfolioForm(request.POST, instance=portfolio)
        if form.is_valid():
            form.save()
            return redirect("crypto_dashboard")
    else:
        form = PortfolioForm(instance=portfolio)
    
    return render(request, "market/edit_portfolio.html", {"form": form})  # Ensure this template name matches!


# Delete Portfolio
@login_required
def delete_portfolio(request, portfolio_id):
    portfolio_item = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    portfolio_item.delete()
    return redirect("crypto_dashboard")