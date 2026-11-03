from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app
from database import SessionLocal


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_product_stock():
    """
    Reset Product 1 stock before every test.

    This prevents one test's checkout from consuming
    stock needed by another test.
    """
    db = SessionLocal()

    try:
        db.execute(
            text(
                "UPDATE products "
                "SET stock_quantity = 100 "
                "WHERE id = 1"
            )
        )

        db.commit()

    finally:
        db.close()


def unique_user(prefix):
    unique_id = uuid4().hex[:8]

    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "OrdersPassword123"
    }


def register_and_login(user):
    register_response = client.post(
        "/register",
        json=user
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": user["username"],
            "password": user["password"]
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_customer_can_view_order_history():
    user = unique_user("orders_history_customer")

    headers = register_and_login(user)

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # View order history
    orders_response = client.get(
        "/orders",
        headers=headers
    )

    assert orders_response.status_code == 200

    orders = orders_response.json()

    assert len(orders) >= 1

    order = next(
        order for order in orders
        if order["order_id"] == order_id
    )

    assert order["order_id"] == order_id
    assert order["status"] == "PLACED"


def test_customer_with_no_orders_gets_empty_order_history():
    user = unique_user("empty_orders_customer")

    headers = register_and_login(user)

    response = client.get(
        "/orders",
        headers=headers
    )

    assert response.status_code == 200

    orders = response.json()

    assert orders == []


def test_customer_can_view_specific_order():
    user = unique_user("specific_order_customer")

    headers = register_and_login(user)

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Get specific order
    response = client.get(
        f"/orders/{order_id}",
        headers=headers
    )

    assert response.status_code == 200

    order = response.json()

    assert order["order_id"] == order_id
    assert order["status"] == "PLACED"


def test_customer_cannot_view_another_users_order():
    user1 = unique_user("order_owner")
    user2 = unique_user("other_customer")

    headers1 = register_and_login(user1)
    headers2 = register_and_login(user2)

    # User 1 adds product to cart
    add_response = client.post(
        "/cart",
        headers=headers1,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    # User 1 creates an order
    checkout_response = client.post(
        "/checkout",
        headers=headers1
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # User 2 tries to view User 1's order
    response = client.get(
        f"/orders/{order_id}",
        headers=headers2
    )

    assert response.status_code == 404


def test_customer_cannot_view_nonexistent_order():
    user = unique_user("nonexistent_order_customer")

    headers = register_and_login(user)

    response = client.get(
        "/orders/999999999",
        headers=headers
    )

    assert response.status_code == 404


def test_unauthenticated_user_cannot_view_orders():
    response = client.get("/orders")

    assert response.status_code == 401


def test_order_total_is_correct():
    user = unique_user("order_total_customer")

    headers = register_and_login(user)

    # Get product price
    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    product = product_response.json()
    product_price = float(product["price"])

    quantity = 2

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": quantity
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Get the order
    order_response = client.get(
        f"/orders/{order_id}",
        headers=headers
    )

    assert order_response.status_code == 200

    order = order_response.json()

    expected_total = product_price * quantity

    assert order["total_amount"] == expected_total


def test_order_contains_correct_item():
    user = unique_user("order_item_customer")

    headers = register_and_login(user)

    # Get product details
    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    product = product_response.json()

    quantity = 2

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": quantity
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Get specific order
    order_response = client.get(
        f"/orders/{order_id}",
        headers=headers
    )

    assert order_response.status_code == 200

    order = order_response.json()

    assert len(order["items"]) == 1

    item = order["items"][0]

    assert item["product_id"] == product["id"]
    assert item["product_name"] == product["name"]
    assert item["quantity"] == quantity


def test_order_item_contains_correct_product_price():
    user = unique_user("order_price_customer")

    headers = register_and_login(user)

    # Get product details before purchase
    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    product = product_response.json()

    expected_price = float(product["price"])

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Retrieve order
    order_response = client.get(
        f"/orders/{order_id}",
        headers=headers
    )

    assert order_response.status_code == 200

    order = order_response.json()

    assert len(order["items"]) == 1

    item = order["items"][0]

    assert item["price"] == expected_price


def test_order_item_total_price_is_correct():
    user = unique_user("order_item_total_customer")

    headers = register_and_login(user)

    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    product = product_response.json()

    quantity = 2
    product_price = float(product["price"])

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": quantity
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Get order
    order_response = client.get(
        f"/orders/{order_id}",
        headers=headers
    )

    assert order_response.status_code == 200

    order = order_response.json()

    assert len(order["items"]) == 1

    item = order["items"][0]

    expected_total = product_price * quantity

    assert item["total_price"] == expected_total


def test_customer_can_have_multiple_orders():
    user = unique_user("multiple_orders_customer")

    headers = register_and_login(user)

    # First order
    add_response_1 = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response_1.status_code == 200

    checkout_response_1 = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response_1.status_code == 200

    order_id_1 = checkout_response_1.json()["order_id"]

    # Second order
    add_response_2 = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response_2.status_code == 200

    checkout_response_2 = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response_2.status_code == 200

    order_id_2 = checkout_response_2.json()["order_id"]

    # Get order history
    orders_response = client.get(
        "/orders",
        headers=headers
    )

    assert orders_response.status_code == 200

    orders = orders_response.json()

    order_ids = [
        order["order_id"]
        for order in orders
    ]

    assert order_id_1 in order_ids
    assert order_id_2 in order_ids
    assert order_id_1 != order_id_2

def test_admin_can_view_all_orders():
    customer = unique_user("admin_orders_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("orders_admin")

    admin_register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register_response.status_code == 200

    # Login as admin
    admin_login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login_response.status_code == 200

    admin_token = admin_login_response.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    # Admin views all orders
    orders_response = client.get(
        "/admin/orders",
        headers=admin_headers
    )

    assert orders_response.status_code == 200

    orders = orders_response.json()

    order_ids = [
        order["order_id"]
        for order in orders
    ]

    assert order_id in order_ids

def test_customer_cannot_view_all_orders():
    customer = unique_user("normal_customer")

    customer_headers = register_and_login(customer)

    response = client.get(
        "/admin/orders",
        headers=customer_headers
    )

    assert response.status_code == 403

def test_admin_can_update_order_status():
    customer = unique_user("status_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("status_admin")

    admin_register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register_response.status_code == 200

    # Login as admin
    admin_login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login_response.status_code == 200

    admin_token = admin_login_response.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    # Admin updates order status
    update_response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert update_response.status_code == 200

    result = update_response.json()

    assert result["order_id"] == order_id
    assert result["status"] == "CONFIRMED"

def test_customer_can_see_updated_order_status():
    customer = unique_user("updated_status_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("updated_status_admin")

    admin_register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register_response.status_code == 200

    # Login as admin
    admin_login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login_response.status_code == 200

    admin_token = admin_login_response.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    # Admin changes status
    update_response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert update_response.status_code == 200

    # Customer checks the order
    order_response = client.get(
        f"/orders/{order_id}",
        headers=customer_headers
    )

    assert order_response.status_code == 200

    order = order_response.json()

    assert order["order_id"] == order_id
    assert order["status"] == "CONFIRMED"

def test_admin_cannot_skip_order_status():
    customer = unique_user("skip_status_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("skip_status_admin")

    admin_register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register_response.status_code == 200

    # Login as admin
    admin_login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login_response.status_code == 200

    admin_token = admin_login_response.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    # Try to skip CONFIRMED and directly move to SHIPPED
    update_response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "SHIPPED"
        }
    )

    assert update_response.status_code == 400

def test_admin_can_complete_order_status_flow():
    customer = unique_user("complete_flow_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("complete_flow_admin")

    admin_register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register_response.status_code == 200

    # Login as admin
    admin_login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login_response.status_code == 200

    admin_token = admin_login_response.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    # PLACED -> CONFIRMED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"

    # CONFIRMED -> SHIPPED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "SHIPPED"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SHIPPED"

    # SHIPPED -> DELIVERED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "DELIVERED"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"

def test_delivered_order_cannot_be_changed():
    customer = unique_user("delivered_customer")

    customer_headers = register_and_login(customer)

    # Create order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("delivered_admin")

    register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert login_response.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # PLACED -> CONFIRMED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "CONFIRMED"}
    )

    assert response.status_code == 200

    # CONFIRMED -> SHIPPED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "SHIPPED"}
    )

    assert response.status_code == 200

    # SHIPPED -> DELIVERED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "DELIVERED"}
    )

    assert response.status_code == 200

    # Try to change DELIVERED -> CONFIRMED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "CONFIRMED"}
    )

    assert response.status_code == 400

def test_customer_cannot_update_order_status():
    customer = unique_user("customer_status_update")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Customer tries to change their own order status
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=customer_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 403

def test_unauthenticated_user_cannot_update_order_status():
    response = client.put(
        "/admin/orders/1/status",
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 401

def test_customer_can_cancel_placed_order():
    customer = unique_user("cancel_order_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("cancel_order_admin")

    register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert login_response.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # Admin cancels the order
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CANCELLED"
        }
    )

    assert response.status_code == 200

    result = response.json()

    assert result["order_id"] == order_id
    assert result["status"] == "CANCELLED"

    # Customer verifies the status
    order_response = client.get(
        f"/orders/{order_id}",
        headers=customer_headers
    )

    assert order_response.status_code == 200

    order = order_response.json()

    assert order["status"] == "CANCELLED"

def test_cancelled_order_cannot_be_changed():
    customer = unique_user("cancelled_terminal_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("cancelled_terminal_admin")

    register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert login_response.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # PLACED -> CANCELLED
    cancel_response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CANCELLED"
        }
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"

    # Try CANCELLED -> CONFIRMED
    update_response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert update_response.status_code == 400

def test_admin_cannot_update_nonexistent_order():
    admin = unique_user("nonexistent_order_admin")

    register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert login_response.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # Try to update an order that does not exist
    response = client.put(
        "/admin/orders/999999999/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 404

def test_customer_cannot_update_another_users_order():
    customer1 = unique_user("order_owner_status")
    customer2 = unique_user("other_customer_status")

    headers1 = register_and_login(customer1)
    headers2 = register_and_login(customer2)

    # Customer 1 creates an order
    add_response = client.post(
        "/cart",
        headers=headers1,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=headers1
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Customer 2 tries to update Customer 1's order
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=headers2,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 403

def test_admin_can_ship_confirmed_order():
    customer = unique_user("ship_order_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("ship_order_admin")

    register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert login_response.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # PLACED -> CONFIRMED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 200

    # CONFIRMED -> SHIPPED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "SHIPPED"
        }
    )

    assert response.status_code == 200

    result = response.json()

    assert result["order_id"] == order_id
    assert result["status"] == "SHIPPED"

def test_shipped_order_cannot_go_back_to_confirmed():
    customer = unique_user("shipped_backward_customer")

    customer_headers = register_and_login(customer)

    # Customer creates an order
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    checkout_response = client.post(
        "/checkout",
        headers=customer_headers
    )

    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["order_id"]

    # Create admin
    admin = unique_user("shipped_backward_admin")

    register_response = client.post(
        "/admin/register",
        json=admin
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert login_response.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # PLACED -> CONFIRMED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 200

    # CONFIRMED -> SHIPPED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "SHIPPED"
        }
    )

    assert response.status_code == 200

    # Try SHIPPED -> CONFIRMED
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={
            "status": "CONFIRMED"
        }
    )

    assert response.status_code == 400