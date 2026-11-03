from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_get_products():
    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert "products" in data
    assert "page" in data
    assert "limit" in data
    assert "total_products" in data
    assert "total_pages" in data

def test_get_product_by_id():
    response = client.get("/products/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert "name" in data
    assert "description" in data
    assert "price" in data
    assert "category" in data
    assert "stock_quantity" in data

def test_get_product_not_found():
    response = client.get("/products/99999")

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Product not found"

def test_create_product_requires_authentication():
    response = client.post(
        "/products",
        json={
            "name": "Test Product",
            "description": "Test product description",
            "price": 1000,
            "category": "Test",
            "stock_quantity": 10
        }
    )

    assert response.status_code == 401

def test_customer_cannot_create_product():
    username = "product_test_customer"
    password = "TestPassword123"

    register_response = client.post(
        "/register",
        json={
            "username": username,
            "email": "product_test_customer@example.com",
            "password": password
        }
    )

    # If the user already exists from a previous test run,
    # registration can be skipped.
    if register_response.status_code not in [200, 400]:
        assert False, register_response.text

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Customer Product",
            "description": "Should not be created by customer",
            "price": 1000,
            "category": "Test",
            "stock_quantity": 10
        }
    )

    assert response.status_code == 403

def test_admin_can_create_product():
    username = "product_test_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "product_test_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Test Admin Product",
            "description": "Product created during automated testing",
            "price": 1500,
            "category": "Testing",
            "stock_quantity": 10
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Admin Product"
    assert data["price"] == 1500
    assert data["category"] == "Testing"
    assert data["stock_quantity"] == 10

def test_create_product_invalid_price():
    response = client.post(
        "/products",
        json={
            "name": "Invalid Product",
            "description": "Product with invalid price",
            "price": 0,
            "category": "Testing",
            "stock_quantity": 10
        }
    )

    assert response.status_code == 401

def test_admin_cannot_create_product_with_invalid_price():
    username = "validation_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "validation_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Invalid Price Product",
            "description": "Price should be greater than zero",
            "price": 0,
            "category": "Testing",
            "stock_quantity": 10
        }
    )

    assert response.status_code == 422

def test_admin_cannot_create_product_with_negative_stock():
    username = "stock_validation_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "stock_validation_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Invalid Stock Product",
            "description": "Stock cannot be negative",
            "price": 1000,
            "category": "Testing",
            "stock_quantity": -5
        }
    )

    assert response.status_code == 422

def test_admin_can_update_product():
    username = "update_product_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "update_product_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/products/1",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Updated Samsung Phone",
            "description": "Updated product description",
            "price": 27000,
            "category": "Mobiles"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Updated Samsung Phone"
    assert data["description"] == "Updated product description"
    assert data["price"] == 27000
    assert data["category"] == "Mobiles"

def test_customer_cannot_update_product():
    username = "update_customer"
    password = "CustomerPassword123"

    register_response = client.post(
        "/register",
        json={
            "username": username,
            "email": "update_customer@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/products/1",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Unauthorized Update",
            "description": "Customer should not update this",
            "price": 9999,
            "category": "Testing"
        }
    )

    assert response.status_code == 403

def test_admin_update_product_not_found():
    username = "update_not_found_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "update_not_found_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/products/99999",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Does Not Exist",
            "description": "Testing nonexistent product",
            "price": 1000,
            "category": "Testing"
        }
    )

    assert response.status_code == 404

def test_admin_can_delete_product():
    username = "delete_product_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "delete_product_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Create a product specifically for this test
    create_response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Product To Delete",
            "description": "This product will be deleted",
            "price": 1000,
            "category": "Testing",
            "stock_quantity": 5
        }
    )

    assert create_response.status_code == 200

    product_id = create_response.json()["id"]

    # Delete the product
    delete_response = client.delete(
        f"/products/{product_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert delete_response.status_code == 200

def test_customer_cannot_delete_product():
    username = "delete_customer"
    password = "CustomerPassword123"

    register_response = client.post(
        "/register",
        json={
            "username": username,
            "email": "delete_customer@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.delete(
        "/products/1",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

def test_admin_delete_product_not_found():
    username = "delete_not_found_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "delete_not_found_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.delete(
        "/products/99999",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 404

def test_admin_can_restock_product():
    username = "restock_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "restock_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    product_response = client.get("/products/1")
    assert product_response.status_code == 200

    old_stock = product_response.json()["stock_quantity"]

    response = client.put(
        "/admin/products/1/stock",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 200

    print("RESTOCK RESPONSE:", response.json())
    data = response.json()

def test_customer_cannot_restock_product():
    username = "restock_customer"
    password = "CustomerPassword123"

    register_response = client.post(
        "/register",
        json={
            "username": username,
            "email": "restock_customer@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/admin/products/1/stock",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 403

def test_unauthenticated_user_cannot_restock_product():
    response = client.put(
        "/admin/products/1/stock",
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 401

def test_admin_restock_product_not_found():
    username = "restock_not_found_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "restock_not_found_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/admin/products/99999/stock",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 404

def test_admin_cannot_restock_with_zero_quantity():
    username = "invalid_restock_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "invalid_restock_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/admin/products/1/stock",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 0
        }
    )

    assert response.status_code == 422

def test_admin_cannot_restock_with_negative_quantity():
    username = "negative_restock_admin"
    password = "AdminPassword123"

    register_response = client.post(
        "/admin/register",
        json={
            "username": username,
            "email": "negative_restock_admin@example.com",
            "password": password
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.put(
        "/admin/products/1/stock",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": -5
        }
    )

    assert response.status_code == 422