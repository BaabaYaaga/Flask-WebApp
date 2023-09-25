Flask Web Application

Description

This web application is built using Flask and provides a simple eCommerce platform. Users can register, login, browse products by category, and make purchases. It also features a cart system for storing items before purchasing.

Project Structure

- Controllers: All the routes are defined in the main Python file (e.g., `app.py`).
- Templates: HTML templates are stored in the `templates` folder.
- Models: Models for the application are defined separately, which interact with the database.

Features

Default Features

1. User Authentication: The application supports user registration and login functionalities.
2. Product Listing: Products are listed based on categories.
3. Dashboard: Authenticated users can access a dashboard that displays available products.
4. Shopping Cart: Users can add items to a shopping cart.

Additional Features

1. Profile Management: Users can update their profiles.
2. Checkout: Users can checkout all items from the cart.
3. Sales Register: All sales are registered in a Sales Register model.

Getting Started

Prerequisites

- Python 3.x
- pip
- Virtualenv

Installation

1. Clone this repository.
2. Navigate to the project directory and create a virtual environment:

    ```
    python -m venv venv
    ```

3. Activate the virtual environment:

    - On Windows: `venv\Scripts\activate`
    - On macOS and Linux: `source venv/bin/activate`

4. Install the required packages:

    ```
    pip install -r requirements.txt
    ```

5. Run the Flask application:

    ```
    python app.py
    ```

Now the server should be running at `http://127.0.0.1:5000/`

API Documentation

Refer to the `API.yaml` file for detailed API specifications.

Author
Ajit Jha