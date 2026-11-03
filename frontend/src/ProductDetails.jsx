import { useEffect, useState } from 'react'
import './App.css'

function ProductDetails({ productId, onBack }) {
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [cartMessage, setCartMessage] = useState('')
  const [cartError, setCartError] = useState('')
  const [addingToCart, setAddingToCart] = useState(false)

  useEffect(() => {
    async function fetchProduct() {
      setLoading(true)
      setError('')
      setProduct(null)
      setQuantity(1)
      setCartMessage('')
      setCartError('')

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/products/${productId}`
        )

        if (!response.ok) {
          throw new Error('Product not found')
        }

        const data = await response.json()
        setProduct(data)
      } catch {
        setError('Unable to load product details.')
      } finally {
        setLoading(false)
      }
    }

    fetchProduct()
  }, [productId])

  async function handleAddToCart() {
    setCartMessage('')
    setCartError('')

    const token = localStorage.getItem('access_token')

    if (!token) {
      setCartError('Please log in as a customer before adding products to your cart.')
      return
    }

    if (quantity < 1 || quantity > product.stock_quantity) {
      setCartError('Please select a valid quantity within the available stock.')
      return
    }

    setAddingToCart(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          product_id: product.id,
          quantity: quantity,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Unable to add product to cart.'
        )
      }

      setCartMessage('Product added to your cart successfully!')
    } catch (err) {
      setCartError(err.message || 'Unable to add product to cart.')
    } finally {
      setAddingToCart(false)
    }
  }

  if (loading) {
    return <p>Loading product details...</p>
  }

  if (error) {
    return (
      <section className="product-details">
        <p className="error-message">{error}</p>
        <button onClick={onBack}>Back to Products</button>
      </section>
    )
  }

  if (!product) {
    return null
  }

  const outOfStock = product.stock_quantity <= 0

  return (
    <section className="product-details">
      <button onClick={onBack}>← Back to Products</button>

      <div className="product-details-content">
        <div className="product-details-image">🛍️</div>

        <div className="product-details-info">
          <p className="product-category">{product.category}</p>

          <h2>{product.name}</h2>

          <p className="product-description">
            {product.description || 'No description available.'}
          </p>

          <h3 className="product-price">
            ₹{Number(product.price).toLocaleString('en-IN')}
          </h3>

          <p
            className={
              outOfStock
                ? 'stock unavailable'
                : 'stock available'
            }
          >
            {outOfStock
              ? 'Out of Stock'
              : `In Stock (${product.stock_quantity})`}
          </p>

          {!outOfStock && (
            <div className="quantity-control">
              <label htmlFor="product-quantity">
                Quantity:
              </label>

              <select
                id="product-quantity"
                value={quantity}
                onChange={(event) => {
                  setQuantity(Number(event.target.value))
                  setCartMessage('')
                  setCartError('')
                }}
                disabled={addingToCart}
              >
                {Array.from(
                  { length: Math.min(product.stock_quantity, 10) },
                  (_, index) => index + 1
                ).map((number) => (
                  <option key={number} value={number}>
                    {number}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            type="button"
            className="add-to-cart-button"
            onClick={handleAddToCart}
            disabled={outOfStock || addingToCart}
          >
            {outOfStock
              ? 'Out of Stock'
              : addingToCart
                ? 'Adding to Cart...'
                : 'Add to Cart'}
          </button>

          {cartMessage && (
            <p className="cart-success-message" role="status">
              {cartMessage}
            </p>
          )}

          {cartError && (
            <p className="error-message" role="alert">
              {cartError}
            </p>
          )}
        </div>
      </div>
    </section>
  )
}

export default ProductDetails
