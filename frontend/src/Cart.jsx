import { useEffect, useState } from 'react'

function Cart({ onBack }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busyItemId, setBusyItemId] = useState(null)

  const fetchCart = async (showLoader = true) => {
    if (showLoader) setLoading(true)
    setError('')

    try {
      const token = localStorage.getItem('access_token')

      if (!token) {
        setProducts([])
        setError('Please log in to view your cart.')
        return
      }

      const response = await fetch('http://127.0.0.1:8000/cart', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to load cart.')
      }

      setProducts(Array.isArray(data) ? data : data.products || [])
    } catch (err) {
      setError(err.message || 'Could not load your cart.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCart()
  }, [])

  async function updateQuantity(product, newQuantity) {
    const itemId = product.cart_item_id ?? product.id

    if (!itemId || newQuantity < 1) return

    const stock = product.available_stock ?? product.stock_quantity

    if (stock != null && newQuantity > stock) {
      setError(`Only ${stock} units are currently available.`)
      return
    }

    const token = localStorage.getItem('access_token')

    if (!token) {
      setError('Please log in to update your cart.')
      return
    }

    setBusyItemId(itemId)
    setError('')
    setMessage('')

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/cart/${itemId}`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ quantity: newQuantity }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update quantity.')
      }

      await fetchCart(false)
      setMessage('Cart quantity updated successfully.')
    } catch (err) {
      setError(err.message || 'Could not update quantity.')
    } finally {
      setBusyItemId(null)
    }
  }

  async function removeItem(product) {
    const itemId = product.cart_item_id ?? product.id

    if (!itemId) {
      setError('Could not identify this cart item.')
      return
    }

    const token = localStorage.getItem('access_token')

    if (!token) {
      setError('Please log in to remove cart items.')
      return
    }

    setBusyItemId(itemId)
    setError('')
    setMessage('')

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/cart/${itemId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to remove item.')
      }

      await fetchCart(false)
      setMessage('Product removed from your cart.')
    } catch (err) {
      setError(err.message || 'Could not remove the item.')
    } finally {
      setBusyItemId(null)
    }
  }

  const total = products.reduce(
    (sum, product) =>
      sum +
      Number(
        product.total_price ??
          Number(product.price || 0) * Number(product.quantity || 0)
      ),
    0
  )

  return (
    <section className="cart-section">
      <button type="button" onClick={onBack} className="back-button">
        ← Back to Store
      </button>

      <h2>Shopping Cart</h2>

      {loading && <p>Loading your cart...</p>}
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      {!loading && !error && products.length === 0 && (
        <p>Your cart is empty.</p>
      )}

      {!loading && products.length > 0 && (
        <>
          <div className="cart-items">
            {products.map((product) => {
              const itemId = product.cart_item_id ?? product.id
              const quantity = Number(product.quantity || 1)
              const stock =
                product.available_stock ?? product.stock_quantity
              const isBusy = busyItemId === itemId

              return (
                <article className="cart-item" key={itemId}>
                  <div>
                    <h3>{product.product_name || product.name}</h3>

                    {product.category && <p>{product.category}</p>}

                    <p>
                      Price: ₹
                      {Number(product.price || 0).toLocaleString('en-IN')}
                    </p>

                    <div className="cart-quantity">
                      <button
                        type="button"
                        disabled={isBusy || quantity <= 1}
                        onClick={() => updateQuantity(product, quantity - 1)}
                      >
                        −
                      </button>

                      <span>Quantity: {quantity}</span>

                      <button
                        type="button"
                        disabled={
                          isBusy ||
                          (stock != null && quantity >= stock)
                        }
                        onClick={() => updateQuantity(product, quantity + 1)}
                      >
                        +
                      </button>
                    </div>

                    <p>
                      Stock: {stock === 0 ? 'Out of stock' : stock ?? 'Unknown'}
                    </p>

                    <p>
                      Item Total: ₹
                      {Number(
                        product.total_price ??
                          Number(product.price || 0) * quantity
                      ).toLocaleString('en-IN')}
                    </p>

                    <button
                      type="button"
                      className="remove-cart-button"
                      disabled={isBusy}
                      onClick={() => removeItem(product)}
                    >
                      {isBusy ? 'Please wait...' : 'Remove'}
                    </button>
                  </div>
                </article>
              )
            })}
          </div>

          <div className="cart-summary">
            <h3>Cart Total: ₹{total.toLocaleString('en-IN')}</h3>

            <button type="button" onClick={() => fetchCart()} disabled={loading}>
              Refresh Cart
            </button>
          </div>
        </>
      )}
    </section>
  )
}

export default Cart