from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from collections import defaultdict
from sqlalchemy import func
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'IIT_M_MAD_Assignment'


#Databases
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file in project directory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Silence the deprecation warning

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    user_type = db.Column(db.String(60), nullable=False)
    age = db.Column(db.Integer, nullable=False, default=0)
    def __repr__(self):
        return f"User('{self.username}')"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    rate_per_unit = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    Manufacturing_Date = db.Column(db.Date, default='2023-09-24')
    Expiry_Date = db.Column(db.Date, default='2023-09-24')

    def __repr__(self):
        return f"Product('{self.name}', '{self.unit}', '{self.rate_per_unit}', '{self.quantity}')"


class SalesRegister(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    quantity_purchased = db.Column(db.Integer, nullable=False)

# Home page route

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # we are here checking if user is in database
        existing_user = User.query.filter_by(username=username).first()

        if existing_user and existing_user.password == password:
            # once login is successful, we can redirect the user to the dashboard
            session['logged_in'] = True
            session['username'] = existing_user.username
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid username or password", "danger")
            return render_template('index.html')
    return render_template('index.html')

# Registration section - this is for new user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is not None:
            flash("Username already exists. Choose another username.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Password doesn't match with confirm password, Retry!!!", "danger")
            return render_template('register.html')

        # Create a new user and add to the database
        new_user = User(username=username, password=password, user_type='Customer')
        db.session.add(new_user)
        db.session.commit()

        flash("Successfully registered! You can now login.", "success")
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/user_dashboard', methods=['GET'])
def user_dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('home'))

    max_price = request.args.get('price')
    selected_category = request.args.get('category')
    min_expiry_date_str = request.args.get('min_expiry_date')

    categories = Category.query.all()
    category_dict = {}

    min_expiry_date = None

    if min_expiry_date_str:
        min_expiry_date = datetime.strptime(min_expiry_date_str, '%Y-%m-%d').date()

    for category in categories:
        if selected_category and category.name != selected_category:
            continue
        products = category.products
        if max_price:
            products = [p for p in products if p.rate_per_unit <= float(max_price)]
        if min_expiry_date:
            products = [p for p in products if p.Expiry_Date >= min_expiry_date]
        category_dict[category.name] = products

    return render_template('user_dashboard.html', categories=category_dict)


@app.route('/buy_section/<item_name>', methods=['GET', 'POST'])
def buy_section(item_name):
    if 'logged_in' not in session:
        flash("Wrong username or password", 'danger')
        return redirect(url_for('home'))
    product = Product.query.filter_by(name=item_name).first()

    if product is None:
        return "Product not found", 404

    if request.method == 'POST':
        quantity_purchased = int(request.form['quantity'])

        if product and (product.quantity - quantity_purchased >= 0):
            product.quantity -= quantity_purchased

            sale = SalesRegister(product_name=item_name, quantity_purchased=quantity_purchased)
            db.session.add(sale)

            db.session.commit()

            return render_template('confirmation.html', message="Thanks for your purchase!!")

        elif product and (product.quantity - quantity_purchased < 0):
            flash(f"You can only buy up to {product.quantity} units.", 'danger')
            return redirect(url_for('user_dashboard'))
        else:
            return flash("Product not found", 'Success')

    # GET Request - For Loading
    availability = "In Stock" if product.quantity > 0 else "Out of Stock"
    rate_per_unit = product.rate_per_unit

    category = Category.query.filter_by(id=product.category_id).first()
    category_name = category.name if category else "Unknown"

    return render_template(
        'buy_section.html',
        item_name=item_name,
        availability=availability,
        price=rate_per_unit,
        category=category_name
    )

@app.route('/profile', methods=['GET'])
def profile():
    if 'username' in session:
        return render_template('profile.html', current_username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'logged_in' not in session:
        return redirect(url_for('home'))

    new_username = request.form['username']
    new_password = request.form['password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return redirect(url_for('profile'))
    user = User.query.filter_by(username=session['username']).first()
    if user:
        user.username = new_username
        user.password = new_password
        db.session.commit()

        session['username'] = new_username
        flash('Profile updated successfully!', 'success')
    else:
        flash('Error updating profile', 'error')

    return redirect(url_for('profile'))

@app.route('/add_to_cart/<item_name>')
def add_to_cart(item_name):
    if 'cart' not in session:
        session['cart'] = []

    product = Product.query.filter_by(name=item_name).first()
    category = Category.query.filter_by(id=product.category_id).first()
    category_name = category.name
    item = {'name': item_name, 'price': product.rate_per_unit, 'category': category_name}

    session['cart'].append(item)
    session.modified = True
    flash(f"{item_name} added to the cart", 'info')
    return redirect(url_for('user_dashboard'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    return render_template('cart.html', cart_items=cart_items)


@app.route('/checkout', methods=['POST'])
def checkout():
    quantities = {}
    for key, value in request.form.items():
        if key.startswith('quantity_'):
            product_name = key.split('quantity_')[1]
            quantities[product_name] = int(value)

    error_flag = False

    for key, value in quantities.items():
        product = Product.query.filter_by(name=key).first()

        if product is None:
            return "Product not found", 404

        if request.method == 'POST':
            quantity_purchased = int(value)

            if product and (product.quantity - quantity_purchased >= 0):

                product.quantity -= quantity_purchased


                sale = SalesRegister(product_name=key, quantity_purchased=quantity_purchased)
                db.session.add(sale)


                db.session.commit()

            elif product and (product.quantity - quantity_purchased < 0):
                flash(f"You can only buy up to {product.quantity} units of {product.name}. Retry", 'danger')
                error_flag = True

    if not error_flag:

        session['cart'] = []

    if error_flag:
        return redirect(url_for('cart'))
    else:
        return render_template('confirmation.html', message="Thanks for your purchase!!")

@app.route('/logout_user')
def logout_user():
    session.clear()
    return redirect(url_for('home'))

@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.password == password and existing_user.user_type == 'manager':
            session['logged_in'] = True
            return redirect(url_for('manager_dashboard'))
        else:
            flash("Invalid username or password", "error")
            return render_template('index.html')  # Assuming login template is 'user_login.html'
    else:
        return render_template('manager_login.html')

@app.route('/manager_dashboard', methods=['GET', 'POST'])
def manager_dashboard():
    if 'logged_in' in session:
        if request.method == 'POST':
            new_category_name = request.form.get('new_category')
            if new_category_name:
                existing_category = Category.query.filter_by(name=new_category_name).first()
                if existing_category is None:
                    new_category = Category(name=new_category_name)
                    db.session.add(new_category)
                    db.session.commit()
                    flash("Category added successfully.", 'success')
                else:
                    flash("Category already exists.", 'error')

        categories = Category.query.all()
        category_dict = {}
        for category in categories:
            category_dict[category.name] = category.products

        return render_template('manager_dashboard.html', categories=category_dict)
    else:
        flash("Please enter valid username or password.", 'danger')
        return redirect(url_for('manager_login'))

@app.route('/add_category', methods=['POST'])
def add_category():
    new_category = request.form.get('new_category')
    existing_category = Category.query.filter_by(name=new_category).first()

    if new_category and not existing_category:
        db_category = Category(name=new_category)
        db.session.add(db_category)
        db.session.commit()
        flash("Category added successfully.", 'success')
        return redirect(url_for('manager_dashboard'))  # Replace with your dashboard URL
    else:
        flash("Category already exists or input was invalid.", 'error')
        return redirect(url_for('manager_dashboard'))  # Replace with your dashboard URL


@app.route('/add_product/<category>', methods=['GET', 'POST'])
def add_product(category):
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        unit = request.form.get('unit')
        rate = request.form.get('rate')
        quantity = request.form.get('quantity')
        manufacturing_date = request.form.get('manufacturing_date')
        expiry_date = request.form.get('expiry_date')
        db_category = Category.query.filter_by(name=category).first()

        if not all([product_name, unit, rate, quantity, manufacturing_date, expiry_date]):
            flash('All fields are required!', 'danger')
            return render_template('add_product.html')
        if not db_category:
            flash("Category does not exist.", 'error')
            return redirect(url_for('manager_dashboard'))
        manufacturing_date = datetime.strptime(manufacturing_date, '%Y-%m-%d').date()
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        new_product = Product(name=product_name,unit=unit,rate_per_unit=rate,quantity=quantity,Manufacturing_Date=manufacturing_date,Expiry_Date=expiry_date, category_id=db_category.id)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully.", 'success')
        return redirect(url_for('manager_dashboard'))
    return render_template('add_product.html', category=category)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get(product_id)

    if product is None:
        flash("Product not found.")
        return redirect(url_for('manager_dashboard'))

    if request.method == 'POST':
        product.name = request.form.get('product_name')
        product.unit = request.form.get('Unit')
        product.rate_per_unit = request.form.get('Rate')
        product.quantity = request.form.get('Quantity')
        product.Manufacturing_Date = request.form.get('Manufacturing_Date')
        product.Expiry_Date = request.form.get('Expiry_Date')

        product.Manufacturing_Date = datetime.strptime(product.Manufacturing_Date, '%Y-%m-%d').date()
        product.Expiry_Date = datetime.strptime(product.Expiry_Date, '%Y-%m-%d').date()
        if not all([product.name, product.unit, product.rate_per_unit, product.quantity, product.Manufacturing_Date, product.Expiry_Date]):
            flash('All fields are required!', 'danger')
        else:
            db.session.commit()
            flash('Product updated successfully.','success')
            return redirect(url_for('manager_dashboard'))

    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)

    if product is None:
        flash("Product not found.")
        return redirect(url_for('manager_dashboard'))

    if request.method == 'POST':
        db.session.delete(product)
        db.session.commit()

        flash('Product deleted successfully.','success')
        return redirect(url_for('manager_dashboard'))

    return render_template('confirm_delete.html', product=product)

@app.route('/update_category/<string:category>', methods=['GET', 'POST'])
def update_category(category):
    if request.method == 'POST':
        new_category_name = request.form.get('updated_category_name')
        category = Category.query.filter_by(name=category).first()
        if category:
            category.name=new_category_name
            db.session.commit()
            flash("Category name updated successfully.", "success")
            return redirect(url_for('manager_dashboard'))
    return render_template('manager_dashboard.html')

@app.route('/delete_category/<string:category>', methods=['GET'])
def delete_category(category):
    db_category = Category.query.filter_by(name=category).first()

    if db_category:
        products_to_delete = Product.query.filter_by(category_id=db_category.id).all()

        for product in products_to_delete:
            db.session.delete(product)

        db.session.delete(db_category)

        db.session.commit()

        flash("Category and associated products have been deleted", 'success')
    else:
        flash("Category not found", 'error')

    return redirect(url_for('manager_dashboard'))

@app.route('/summary')
def summary():
    category_product_data = defaultdict(list)

    products_with_categories = db.session.query(Product.name, Product.quantity, Category.name).join(Category).all()

    for product_name, product_quantity, category_name in products_with_categories:
        category_product_data[category_name].append({
            'name': product_name,
            'quantity': product_quantity
        })

    category_product_data = dict(category_product_data)
    sales_data = []

    sales_records = db.session.query(
        SalesRegister.product_name,
        func.sum(SalesRegister.quantity_purchased)
    ).group_by(
        SalesRegister.product_name,
    ).all()

    for record in sales_records:
        product_name,  total_quantity = record
        sales_data.append({
            'product': product_name,
            'quantity': total_quantity,
        })

    return render_template('summary.html', category_product_data=category_product_data, sales_data=sales_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('manager_login'))

if __name__ == '__main__':
    app.run(debug=True)


