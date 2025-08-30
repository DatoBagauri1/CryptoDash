from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import User
from api_service import crypto_api
import logging

logger = logging.getLogger(__name__)

# Blueprint definitions
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
news_bp = Blueprint('news', __name__)
charts_bp = Blueprint('charts', __name__)
sentiment_bp = Blueprint('sentiment', __name__)
converter_bp = Blueprint('converter', __name__)
leaderboard_bp = Blueprint('leaderboard', __name__)

# Main routes
@main_bp.route('/')
def index():
    trending_coins = crypto_api.get_trending_coins()
    top_coins = crypto_api.get_top_coins(limit=10)
    fear_greed = crypto_api.get_fear_greed_index()
    
    return render_template('index.html', 
                         trending_coins=trending_coins,
                         top_coins=top_coins,
                         fear_greed=fear_greed)

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# Dashboard routes
@dashboard_bp.route('/')
def dashboard():
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'market_cap')
    
    if filter_type == 'volume':
        order = 'volume_desc'
    elif filter_type == 'price_change':
        order = 'price_change_percentage_24h_desc'
    else:
        order = 'market_cap_desc'
    
    top_coins = crypto_api.get_top_coins(limit=50, page=page)
    
    # Sort based on filter
    if filter_type == 'price_change' and top_coins:
        top_coins = sorted(top_coins, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
    
    return render_template('dashboard.html', 
                         top_coins=top_coins,
                         current_filter=filter_type)


# News routes
@news_bp.route('/')
def news():
    news_items = crypto_api.get_crypto_news(limit=30)
    return render_template('news.html', news_items=news_items)

# Charts routes
@charts_bp.route('/')
def charts():
    coin_id = request.args.get('coin', 'bitcoin')
    days = request.args.get('days', 30, type=int)
    
    # Get historical data
    historical_data = crypto_api.get_coin_history(coin_id, days)
    
    # Get current coin info
    coin_prices = crypto_api.get_coin_prices([coin_id])
    coin_info = coin_prices.get(coin_id, {}) if coin_prices else {}
    
    return render_template('charts.html', 
                         historical_data=historical_data,
                         coin_id=coin_id,
                         coin_info=coin_info,
                         days=days)

# Sentiment routes
@sentiment_bp.route('/')
def sentiment():
    fear_greed = crypto_api.get_fear_greed_index()
    return render_template('sentiment.html', fear_greed=fear_greed)

# Converter routes
@converter_bp.route('/')
def converter():
    exchange_rates = crypto_api.get_exchange_rates()
    return render_template('converter.html', exchange_rates=exchange_rates)

@converter_bp.route('/convert')
def convert():
    from_currency = request.args.get('from', 'bitcoin')
    to_currency = request.args.get('to', 'usd')
    amount = float(request.args.get('amount', 1))
    
    # Get conversion rates
    rates = crypto_api.get_exchange_rates()
    
    result = {}
    if from_currency in rates and to_currency in rates[from_currency]:
        conversion_rate = rates[from_currency][to_currency]
        result = {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount,
            'converted_amount': amount * conversion_rate,
            'rate': conversion_rate
        }
    
    return jsonify(result)

# Leaderboard routes
@leaderboard_bp.route('/')
def leaderboard():
    sort_by = request.args.get('sort', '24h_change')
    
    top_coins = crypto_api.get_top_coins(limit=100)
    
    if top_coins:
        if sort_by == '24h_change':
            top_coins = sorted(top_coins, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
        elif sort_by == '7d_change':
            top_coins = sorted(top_coins, key=lambda x: x.get('price_change_percentage_7d_in_currency', 0), reverse=True)
        elif sort_by == 'volume':
            top_coins = sorted(top_coins, key=lambda x: x.get('total_volume', 0), reverse=True)
        # Default is market cap (already sorted)
    
    return render_template('leaderboard.html', 
                         top_coins=top_coins[:50],  # Show top 50
                         sort_by=sort_by)
