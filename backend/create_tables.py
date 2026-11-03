from database import engine, Base
from models import Product, User, CartItem, Order, OrderItem


Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")