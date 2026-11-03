from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def unique_user(prefix):
    unique_id = uuid4().hex[:8]

    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "CartPassword123"
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


def test_customer_can_add_product_to_cart():
    user = unique_user("cart_customer")

    headers = register_and_login(user)

    response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == 1
    assert data["quantity"] == 2


def test_unauthenticated_user_cannot_add_to_cart():
    response = client.post(
        "/cart",
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert response.status_code == 401


def test_customer_cannot_add_nonexistent_product_to_cart():
    user = unique_user("cart_invalid_product_customer")

    headers = register_and_login(user)

    response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 99999,
            "quantity": 1
        }
    )

    assert response.status_code == 404


def test_customer_cannot_add_out_of_stock_product_to_cart():
    customer = unique_user("cart_out_of_stock_customer")
    customer_headers = register_and_login(customer)

    admin = unique_user("cart_stock_admin")

    admin_register = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register.status_code == 200

    admin_login = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login.status_code == 200

    admin_token = admin_login.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    product_response = client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Out Of Stock Test Product",
            "description": "Testing out of stock cart behavior",
            "price": 1000,
            "category": "Test",
            "stock_quantity": 0
        }
    )

    assert product_response.status_code == 200

    product_id = product_response.json()["id"]

    response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": product_id,
            "quantity": 1
        }
    )

    assert response.status_code == 400


def test_customer_cannot_add_more_than_available_stock():
    user = unique_user("cart_stock_limit_customer")

    headers = register_and_login(user)

    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    stock = product_response.json()["stock_quantity"]

    response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": stock + 1
        }
    )

    assert response.status_code == 400


def test_customer_cannot_add_zero_quantity_to_cart():
    user = unique_user("cart_zero_quantity_customer")

    headers = register_and_login(user)

    response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 0
        }
    )

    assert response.status_code == 422


def test_customer_cannot_add_negative_quantity_to_cart():
    user = unique_user("cart_negative_quantity_customer")

    headers = register_and_login(user)

    response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": -1
        }
    )

    assert response.status_code == 422


def test_customer_can_add_same_product_again():
    user = unique_user("cart_duplicate_product_customer")

    headers = register_and_login(user)

    first_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    assert first_data["product_id"] == 1
    assert first_data["quantity"] == 2

    second_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 3
        }
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["product_id"] == 1
    assert second_data["quantity"] == 5

def test_customer_can_view_cart():
    user = unique_user("cart_view_customer")

    headers = register_and_login(user)

    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    response = client.get(
        "/cart",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["product_id"] == 1
    assert data[0]["quantity"] == 2

def test_customer_with_empty_cart_gets_empty_list():
    user = unique_user("empty_cart_customer")

    headers = register_and_login(user)

    response = client.get(
        "/cart",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []

def test_customer_can_only_view_own_cart():
    user_a = unique_user("cart_customer_a")
    user_b = unique_user("cart_customer_b")

    headers_a = register_and_login(user_a)
    headers_b = register_and_login(user_b)

    # Customer A adds a product
    add_response = client.post(
        "/cart",
        headers=headers_a,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    # Customer B views their cart
    response = client.get(
        "/cart",
        headers=headers_b
    )

    assert response.status_code == 200

    data = response.json()

    # Customer B must have an empty cart
    assert data == []

def test_customer_can_update_cart_quantity():
    user = unique_user("cart_update_customer")

    headers = register_and_login(user)

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    # Update quantity
    update_response = client.put(
        f"/cart/{cart_item_id}",
        headers=headers,
        json={
            "quantity": 5
        }
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["cart_item_id"] == cart_item_id
    assert data["product_id"] == 1
    assert data["quantity"] == 5

def test_customer_cannot_update_cart_beyond_available_stock():
    user = unique_user("cart_update_stock_customer")

    headers = register_and_login(user)

    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    stock = product_response.json()["stock_quantity"]

    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    update_response = client.put(
        f"/cart/{cart_item_id}",
        headers=headers,
        json={
            "quantity": stock + 1
        }
    )

    assert update_response.status_code == 400

def test_customer_cannot_update_cart_to_zero_quantity():
    user = unique_user("cart_update_zero_customer")

    headers = register_and_login(user)

    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    update_response = client.put(
        f"/cart/{cart_item_id}",
        headers=headers,
        json={
            "quantity": 0
        }
    )

    assert update_response.status_code == 422


def test_customer_cannot_update_cart_to_negative_quantity():
    user = unique_user("cart_update_negative_customer")

    headers = register_and_login(user)

    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    update_response = client.put(
        f"/cart/{cart_item_id}",
        headers=headers,
        json={
            "quantity": -1
        }
    )

    assert update_response.status_code == 422

def test_customer_cannot_update_nonexistent_cart_item():
    user = unique_user("cart_nonexistent_update_customer")

    headers = register_and_login(user)

    response = client.put(
        "/cart/999999",
        headers=headers,
        json={
            "quantity": 2
        }
    )

    assert response.status_code == 404

def test_customer_cannot_update_another_users_cart_item():
    user_a = unique_user("cart_owner_a")
    user_b = unique_user("cart_owner_b")

    headers_a = register_and_login(user_a)
    headers_b = register_and_login(user_b)

    # Customer A adds a product
    add_response = client.post(
        "/cart",
        headers=headers_a,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    # Customer B tries to update Customer A's cart item
    update_response = client.put(
        f"/cart/{cart_item_id}",
        headers=headers_b,
        json={
            "quantity": 5
        }
    )

    assert update_response.status_code == 404

def test_customer_can_remove_cart_item():
    user = unique_user("cart_remove_customer")

    headers = register_and_login(user)

    # Add product
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    # Remove product
    delete_response = client.delete(
        f"/cart/{cart_item_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    data = delete_response.json()

    assert data["cart_item_id"] == cart_item_id

    # Verify cart is empty
    cart_response = client.get(
        "/cart",
        headers=headers
    )

    assert cart_response.status_code == 200
    assert cart_response.json() == []

def test_customer_cannot_delete_another_users_cart_item():
    user_a = unique_user("cart_delete_owner_a")
    user_b = unique_user("cart_delete_owner_b")

    headers_a = register_and_login(user_a)
    headers_b = register_and_login(user_b)

    # Customer A adds a product
    add_response = client.post(
        "/cart",
        headers=headers_a,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    # Customer B tries to delete Customer A's cart item
    delete_response = client.delete(
        f"/cart/{cart_item_id}",
        headers=headers_b
    )

    assert delete_response.status_code == 404

    # Verify Customer A's cart is still intact
    cart_response = client.get(
        "/cart",
        headers=headers_a
    )

    assert cart_response.status_code == 200

    data = cart_response.json()

    assert len(data) == 1
    assert data[0]["product_id"] == 1
    assert data[0]["quantity"] == 2

def test_customer_cannot_delete_nonexistent_cart_item():
    user = unique_user("cart_delete_nonexistent_customer")

    headers = register_and_login(user)

    response = client.delete(
        "/cart/999999",
        headers=headers
    )

    assert response.status_code == 404

def test_unauthenticated_user_cannot_delete_cart_item():
    user = unique_user("cart_delete_auth_customer")

    headers = register_and_login(user)

    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 1
        }
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["cart_item_id"]

    # Try deleting without authentication
    delete_response = client.delete(
        f"/cart/{cart_item_id}"
    )

    assert delete_response.status_code == 401


def test_customer_can_checkout():
    user = unique_user("checkout_customer")

    headers = register_and_login(user)

    # Get current stock
    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    product = product_response.json()
    original_stock = product["stock_quantity"]

    # Add product to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )

    assert add_response.status_code == 200

    # Checkout
    checkout_response = client.post(
        "/checkout",
        headers=headers
    )

    assert checkout_response.status_code == 200

    data = checkout_response.json()

    assert data["message"] == "Order placed successfully"
    assert "order_id" in data

    expected_total = float(product["price"]) * 2

    assert data["total_amount"] == expected_total
    assert data["status"] == "PLACED"

    # Verify stock was reduced
    updated_product_response = client.get("/products/1")

    assert updated_product_response.status_code == 200

    updated_product = updated_product_response.json()

    assert updated_product["stock_quantity"] == original_stock - 2

    # Verify cart was cleared
    cart_response = client.get(
        "/cart",
        headers=headers
    )

    assert cart_response.status_code == 200
    assert cart_response.json() == []

def test_customer_cannot_checkout_empty_cart():
    user = unique_user("empty_checkout_customer")

    headers = register_and_login(user)

    response = client.post(
        "/checkout",
        headers=headers
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Cart is empty"

def test_customer_cannot_checkout_when_stock_is_insufficient():
    user = unique_user("checkout_stock_customer")

    headers = register_and_login(user)

    # Get current product stock
    product_response = client.get("/products/1")

    assert product_response.status_code == 200

    product = product_response.json()
    stock = product["stock_quantity"]

    # Add more than available stock to cart
    add_response = client.post(
        "/cart",
        headers=headers,
        json={
            "product_id": 1,
            "quantity": stock
        }
    )

    assert add_response.status_code == 200

    # Try to increase cart quantity beyond stock
    update_response = client.put(
        f"/cart/{add_response.json()['cart_item_id']}",
        headers=headers,
        json={
            "quantity": stock + 1
        }
    )

    assert update_response.status_code == 400

def test_checkout_fails_when_stock_becomes_insufficient():
    customer = unique_user("checkout_insufficient_customer")
    customer_headers = register_and_login(customer)

    # Create a separate admin
    admin = unique_user("checkout_stock_admin")

    admin_register = client.post(
        "/admin/register",
        json=admin
    )

    assert admin_register.status_code == 200

    admin_login = client.post(
        "/login",
        json={
            "username": admin["username"],
            "password": admin["password"]
        }
    )

    assert admin_login.status_code == 200

    admin_headers = {
        "Authorization": f"Bearer {admin_login.json()['access_token']}"
    }

    # Create a product with stock = 5
    product_response = client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Checkout Stock Test Product",
            "description": "Testing stock changes before checkout",
            "price": 1000,
            "category": "Test",
            "stock_quantity": 5
        }
    )

    assert product_response.status_code == 200

    product_id = product_response.json()["id"]

    # Customer adds 5 units to cart
    add_response = client.post(
        "/cart",
        headers=customer_headers,
        json={
            "product_id": product_id,
            "quantity": 5
        }
    )

    assert add_response.status_code == 200

    # Admin reduces available stock by restocking only 1 unit less
    stock_response = client.put(
        f"/admin/products/{product_id}/stock",
        headers=admin_headers,
        json={
            "quantity": 1
        }
    )

    assert stock_response.status_code == 200

    # IMPORTANT:
    # The stock endpoint only ADDS stock, so the above would increase
    # stock rather than reduce it.

