from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import jwt

from database import SessionLocal
from models import (
    Product as ProductModel,
    User as UserModel,
    CartItem,
    Order,
    OrderItem
)
from security import hash_password, verify_password
from auth import create_access_token, SECRET_KEY, ALGORITHM
from sqlalchemy import or_


app = FastAPI(title="Online Store API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# JWT SECURITY
# =========================================================

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
):
    # Check whether token was provided

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    # Get JWT token

    token = credentials.credentials

    # Verify JWT

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # Get username from token

    username = payload.get("username")

    if username is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # Find user in database

    user = db.query(UserModel).filter(
        UserModel.username == username
    ).first()

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# =========================================================
# PYDANTIC PRODUCT MODEL
# =========================================================

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0)
    category: str
    stock_quantity: int = Field(ge=0)


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    total_price: float


class OrderResponse(BaseModel):
    order_id: int
    total_amount: float
    status: str
    items: list[OrderItemResponse]


class OrderStatusUpdate(BaseModel):
    status: str


# =========================================================
# PRODUCT UPDATE MODEL
# =========================================================

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    category: str | None = None


# =========================================================
# PRODUCT RESPONSE MODEL
# =========================================================

class ProductResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    page: int
    limit: int
    total_products: int
    total_pages: int


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    cart_item_id: int
    product_id: int
    product_name: str
    price: float
    quantity: int
    available_stock: int
    total_price: float


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class StockUpdate(BaseModel):
    quantity: int = Field(gt=0)


# =========================================================
# USER REGISTRATION MODEL
# =========================================================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


# =========================================================
# USER LOGIN MODEL
# =========================================================

class UserLogin(BaseModel):
    username: str
    password: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Online Store API is running"
    }


# =========================================================
# USER REGISTRATION
# =========================================================

@app.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    # Check whether username already exists

    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Convert plain password into secure Argon2 hash

    hashed_password = hash_password(user.password)

    # Create database user

    new_user = UserModel(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role="CUSTOMER"
    )

    # Save user

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "username": new_user.username,
        "role": new_user.role
    }


# =========================================================
# ADMIN REGISTRATION
# =========================================================

@app.post("/admin/register")
def register_admin(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    existing_email = db.query(UserModel).filter(
        UserModel.email == user.email
    ).first()

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    hashed_password = hash_password(user.password)

    new_admin = UserModel(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role="ADMIN"
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {
        "message": "Admin registered successfully",
        "username": new_admin.username,
        "role": new_admin.role
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    # Find user by username

    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()

    if existing_user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Verify password

    password_correct = verify_password(
        user.password,
        existing_user.password
    )

    if not password_correct:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Create JWT token

    access_token = create_access_token({
        "username": existing_user.username,
        "role": existing_user.role
    })

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "username": existing_user.username,
        "role": existing_user.role
    }


# =========================================================
# CURRENT USER
# =========================================================

@app.get("/me")
def get_me(
    current_user: UserModel = Depends(get_current_user)
):

    return {
        "username": current_user.username,
        "role": current_user.role
    }


# =========================================================
# ADMIN ACCESS
# =========================================================

def require_admin(
    current_user: UserModel = Depends(get_current_user)
):

    if current_user.role != "ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@app.get("/products", response_model=ProductListResponse)
def get_products(
    search: str | None = None,
    category: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db)
):

    # Validate price range

    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):

        raise HTTPException(
            status_code=400,
            detail="min_price cannot be greater than max_price"
        )

    query = db.query(ProductModel)

    # Search

    if search:

        search_pattern = f"%{search}%"

        query = query.filter(
            or_(
                ProductModel.name.ilike(search_pattern),
                ProductModel.description.ilike(search_pattern),
                ProductModel.category.ilike(search_pattern)
            )
        )

    # Category

    if category:

        query = query.filter(
            ProductModel.category.ilike(category)
        )

    # Minimum price

    if min_price is not None:

        query = query.filter(
            ProductModel.price >= min_price
        )

    # Maximum price

    if max_price is not None:

        query = query.filter(
            ProductModel.price <= max_price
        )

    # Sort products by price

    if sort_order == "asc":

        query = query.order_by(
            ProductModel.price.asc(),
            ProductModel.id.asc()
        )

    elif sort_order == "desc":

        query = query.order_by(
            ProductModel.price.desc(),
            ProductModel.id.asc()
        )

    else:

        raise HTTPException(
            status_code=400,
            detail="sort_order must be 'asc' or 'desc'"
        )

    # Total products after filters

    total_products = query.count()

    # Calculate total pages

    total_pages = (total_products + limit - 1) // limit

    # Pagination

    skip = (page - 1) * limit

    products = query.offset(skip).limit(limit).all()

    return {
        "products": products,
        "page": page,
        "limit": limit,
        "total_products": total_products,
        "total_pages": total_pages
    }


# =========================================================
# GET SINGLE PRODUCT
# =========================================================

@app.get(
    "/products/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(ProductModel).filter(
        ProductModel.id == product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# =========================================================
# ADD PRODUCT
# =========================================================

@app.post(
    "/products",
    response_model=ProductResponse
)
def add_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    # Create database product

    new_product = ProductModel(
        name=product.name,
        description=product.description,
        price=product.price,
        category=product.category,
        stock_quantity=product.stock_quantity
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# =========================================================
# UPDATE PRODUCT
# =========================================================

@app.put(
    "/products/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    updated_product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    # Find product

    product = db.query(ProductModel).filter(
        ProductModel.id == product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Get only fields sent by user

    update_data = updated_product.model_dump(
        exclude_unset=True
    )

    # Update fields

    for field, value in update_data.items():

        setattr(product, field, value)

    # Save changes

    db.commit()

    # Refresh object

    db.refresh(product)

    return product


# =========================================================
# ADD PRODUCT STOCK
# =========================================================

@app.put("/admin/products/{product_id}/stock")
def add_product_stock(
    product_id: int,
    stock_data: StockUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    # Find product

    product = db.query(ProductModel).filter(
        ProductModel.id == product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Add new stock

    product.stock_quantity += stock_data.quantity

    db.commit()
    db.refresh(product)

    return {
        "message": "Stock added successfully",
        "product_id": product.id,
        "product_name": product.name,
        "added_quantity": stock_data.quantity,
        "current_stock": product.stock_quantity
    }


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    # Find product

    product = db.query(ProductModel).filter(
        ProductModel.id == product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Delete product

    db.delete(product)

    # Save changes

    db.commit()

    return {
        "message": "Product deleted successfully"
    }


# =========================================================
# CART ITEMS
# =========================================================

@app.post("/cart")
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    # Find product

    product = db.query(ProductModel).filter(
        ProductModel.id == item.product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check stock

    if product.stock_quantity == 0:

        raise HTTPException(
            status_code=400,
            detail="Product is out of stock"
        )

    # Check requested quantity

    if item.quantity > product.stock_quantity:

        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    # Check whether product is already in cart

    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item.product_id
    ).first()

    if existing_item:

        new_quantity = existing_item.quantity + item.quantity

        if new_quantity > product.stock_quantity:

            raise HTTPException(
                status_code=400,
                detail="Total cart quantity exceeds available stock"
            )

        existing_item.quantity = new_quantity

    else:

        new_item = CartItem(
            user_id=current_user.id,
            product_id=item.product_id,
            quantity=item.quantity
        )

        db.add(new_item)

    db.commit()

    if existing_item:
        db.refresh(existing_item)

        return {
            "message": "Product quantity updated in cart",
            "cart_item_id": existing_item.id,
            "product_id": existing_item.product_id,
            "quantity": existing_item.quantity
        }

    db.refresh(new_item)

    return {
        "message": "Product added to cart",
        "cart_item_id": new_item.id,
        "product_id": new_item.product_id,
        "quantity": new_item.quantity
    }


# =========================================================
# GET CART
# =========================================================

@app.get("/cart", response_model=list[CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    cart = []

    for item in cart_items:

        product = db.query(ProductModel).filter(
            ProductModel.id == item.product_id
        ).first()

        if product is None:
            continue

        cart.append({
            "cart_item_id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "price": product.price,
            "quantity": item.quantity,
            "available_stock": product.stock_quantity,
            "total_price": product.price * item.quantity
        })

    return cart


# =========================================================
# UPDATE CART QUANTITY
# =========================================================

@app.put("/cart/{cart_item_id}")
def update_cart_quantity(
    cart_item_id: int,
    item: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id,
        CartItem.user_id == current_user.id
    ).first()

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    product = db.query(ProductModel).filter(
        ProductModel.id == cart_item.product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if item.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    cart_item.quantity = item.quantity

    db.commit()
    db.refresh(cart_item)

    return {
        "message": "Cart quantity updated",
        "cart_item_id": cart_item.id,
        "product_id": cart_item.product_id,
        "quantity": cart_item.quantity
    }

# =========================================================
# REMOVE FROM CART
# =========================================================

@app.delete("/cart/{cart_item_id}")
def remove_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    # Find cart item belonging to the logged-in user

    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id,
        CartItem.user_id == current_user.id
    ).first()

    if cart_item is None:

        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    # Delete cart item

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Product removed from cart",
        "cart_item_id": cart_item_id
    }


# =========================================================
# CHECKOUT
# =========================================================

@app.post("/checkout")
def checkout(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    # Get current user's cart

    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    if not cart_items:

        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # Check all products and stock before creating the order

    order_items_data = []
    total_amount = 0

    for cart_item in cart_items:

        # Lock the product row during checkout
        product = db.query(ProductModel).filter(
            ProductModel.id == cart_item.product_id
        ).with_for_update().first()

        if product is None:

            raise HTTPException(
                status_code=404,
                detail=f"Product {cart_item.product_id} not found"
            )

        if product.stock_quantity < cart_item.quantity:

            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )

        item_total = product.price * cart_item.quantity

        total_amount += item_total

        order_items_data.append({
            "product": product,
            "quantity": cart_item.quantity,
            "item_total": item_total
        })

    # Create order

    new_order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status="PLACED"
    )

    db.add(new_order)
    db.flush()

    # Create order items and reduce stock

    for item in order_items_data:

        product = item["product"]
        quantity = item["quantity"]
        item_total = item["item_total"]

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=quantity,
            total_price=item_total
        )

        db.add(order_item)

        # Reduce stock

        product.stock_quantity -= quantity

    # Clear the cart

    for cart_item in cart_items:

        db.delete(cart_item)

    # Save everything

    db.commit()

    return {
        "message": "Order placed successfully",
        "order_id": new_order.id,
        "total_amount": total_amount,
        "status": new_order.status
    }


# =========================================================
# CUSTOMER ORDERS
# =========================================================

@app.get("/orders", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(
        Order.id.desc()
    ).all()

    result = []

    for order in orders:

        order_items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        items = []

        for item in order_items:

            items.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "price": item.price,
                "quantity": item.quantity,
                "total_price": item.total_price
            })

        result.append({
            "order_id": order.id,
            "total_amount": order.total_amount,
            "status": order.status,
            "items": items
        })

    return result


# =========================================================
# GET SINGLE CUSTOMER ORDER
# =========================================================

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    # Find the order belonging to the logged-in user

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if order is None:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Get order items

    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    items = []

    for item in order_items:

        items.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "price": item.price,
            "quantity": item.quantity,
            "total_price": item.total_price
        })

    return {
        "order_id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
        "items": items
    }


# =========================================================
# ADMIN ORDERS
# =========================================================

@app.get("/admin/orders")
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    orders = db.query(Order).order_by(
        Order.id.desc()
    ).all()

    result = []

    for order in orders:

        order_items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        items = []

        for item in order_items:

            items.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "price": item.price,
                "quantity": item.quantity,
                "total_price": item.total_price
            })

        result.append({
            "order_id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "items": items
        })

    return result


# =========================================================
# ADMIN UPDATE ORDER STATUS
# =========================================================

@app.put("/admin/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    allowed_statuses = [
        "PLACED",
        "CONFIRMED",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED"
    ]

    if status_data.status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if order is None:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    current_status = order.status
    new_status = status_data.status

    valid_transitions = {
        "PLACED": ["CONFIRMED", "CANCELLED"],
        "CONFIRMED": ["SHIPPED", "CANCELLED"],
        "SHIPPED": ["DELIVERED"],
        "DELIVERED": [],
        "CANCELLED": []
    }

    if new_status not in valid_transitions[current_status]:

        raise HTTPException(
            status_code=400,
            detail=f"Cannot change order from {current_status} to {new_status}"
        )

    order.status = new_status

    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status
    }