import { useEffect, useState } from 'react'
import './App.css'
import ProductDetails from './ProductDetails'
import Login from './Login'
import Register from './Register'
import Cart from './Cart'

function App() {
  const [products, setProducts] = useState([])
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [sortOrder, setSortOrder] = useState('asc')
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedProductId, setSelectedProductId] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const [showCart, setShowCart] = useState(false)

  const [currentUser, setCurrentUser] = useState(() => ({
    username: localStorage.getItem('username'),
    role: localStorage.getItem('role'),
  }))

  useEffect(() => {
    async function fetchProducts() {
      setLoading(true)
      setError('')

      try {
        const params = new URLSearchParams({
          page: String(page),
          limit: '10',
          sort_order: sortOrder,
        })

        if (search.trim()) {
          params.set('search', search.trim())
        }

        if (category) {
          params.set('category', category)
        }

        if (minPrice !== '') {
          params.set('min_price', minPrice)
        }

        if (maxPrice !== '') {
          params.set('max_price', maxPrice)
        }

        const response = await fetch(
          `http://127.0.0.1:8000/products?${params.toString()}`
        )

        if (!response.ok) {
          throw new Error('Unable to load products')
        }

        const data = await response.json()

        setProducts(data.products)
        setTotalPages(data.total_pages)
      } catch {
        setError(
          'Could not load products. Please check the backend server.'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchProducts()
  }, [page, search, category, minPrice, maxPrice, sortOrder])

  function clearFilters() {
    setSearch('')
    setCategory('')
    setMinPrice('')
    setMaxPrice('')
    setSortOrder('asc')
    setPage(1)
  }

  function handleLogout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')

    setCurrentUser({
      username: null,
      role: null,
    })

    setSelectedProductId(null)
    setShowLogin(false)
    setShowRegister(false)
    setShowCart(false)
  }

  // Registration page
  if (showRegister) {
    return (
      <div className="store">
        <header className="navbar">
          <h1>Vijay Store</h1>
        </header>

        <main>
          <Register
            onBack={() => setShowRegister(false)}
            onGoToLogin={() => {
              setShowRegister(false)
              setShowLogin(true)
            }}
          />
        </main>

        <footer>
          <p>© 2026 Vijay Store. All rights reserved.</p>
        </footer>
      </div>
    )
  }

  // Login page
  if (showLogin) {
    return (
      <div className="store">
        <header className="navbar">
          <h1>Vijay Store</h1>
        </header>

        <main>
          <Login
            onLoginSuccess={(data) => {
              setCurrentUser({
                username: data.username,
                role: data.role,
              })
              setShowLogin(false)
            }}
            onBack={() => setShowLogin(false)}
          />
        </main>

        <footer>
          <p>© 2026 Vijay Store. All rights reserved.</p>
        </footer>
      </div>
    )
  }

  // Product details page
  if (selectedProductId !== null) {
    return (
      <div className="store">
        <header className="navbar">
          <h1>Vijay Store</h1>

          <nav>
            <button
              type="button"
              onClick={() => setSelectedProductId(null)}
            >
              Back to Store
            </button>

            {currentUser.username ? (
              <>
                <span>Welcome, {currentUser.username}</span>
                <button type="button" onClick={handleLogout}>
                  Logout
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setShowLogin(true)}
                >
                  Login
                </button>
                <button
                  type="button"
                  onClick={() => setShowRegister(true)}
                >
                  Register
                </button>
              </>
            )}
          </nav>
        </header>

        <main>
          <ProductDetails
            productId={selectedProductId}
            onBack={() => setSelectedProductId(null)}
          />
        </main>

        <footer>
          <p>© 2026 Vijay Store. All rights reserved.</p>
        </footer>
      </div>
    )
  }

  // Cart page — outside the Product Details condition
  if (showCart) {
    return (
      <div className="store">
        <header className="navbar">
          <h1>Vijay Store</h1>
        </header>

        <main>
          <Cart onBack={() => setShowCart(false)} />
        </main>

        <footer>
          <p>© 2026 Vijay Store. All rights reserved.</p>
        </footer>
      </div>
    )
  }

  // Main store page
  return (
    <div className="store">
      <header className="navbar">
        <h1>Vijay Store</h1>

        <nav>
          <a href="#home">Home</a>
          <a href="#products">Products</a>

          <button
            type="button"
            onClick={() => setShowCart(true)}
          >
            Cart
          </button>

          {currentUser.username ? (
            <>
              <span>Welcome, {currentUser.username}</span>
              <button type="button" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setShowLogin(true)}
              >
                Login
              </button>

              <button
                type="button"
                onClick={() => setShowRegister(true)}
              >
                Register
              </button>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="hero" id="home">
          <h2>Welcome to Vijay Store</h2>
          <p>Discover quality products at great prices.</p>

          <a className="shop-button" href="#products">
            Shop Now
          </a>
        </section>

        <section className="products" id="products">
          <h2>Our Products</h2>

          <input
            type="text"
            className="search-input"
            placeholder="Search by name, category, or description..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
          />

          <div className="filter-controls">
            <select
              value={category}
              onChange={(event) => {
                setCategory(event.target.value)
                setPage(1)
              }}
            >
              <option value="">All Categories</option>
              <option value="Electronics">Electronics</option>
              <option value="Audio">Audio</option>
              <option value="Test">Test</option>
            </select>

            <input
              type="number"
              min="0"
              placeholder="Minimum price (₹)"
              value={minPrice}
              onChange={(event) => {
                setMinPrice(event.target.value)
                setPage(1)
              }}
            />

            <input
              type="number"
              min="0"
              placeholder="Maximum price (₹)"
              value={maxPrice}
              onChange={(event) => {
                setMaxPrice(event.target.value)
                setPage(1)
              }}
            />

            <select
              value={sortOrder}
              onChange={(event) => {
                setSortOrder(event.target.value)
                setPage(1)
              }}
              aria-label="Sort products by price"
            >
              <option value="asc">Price: Low to High</option>
              <option value="desc">Price: High to Low</option>
            </select>

            <button type="button" onClick={clearFilters}>
              Clear Filters
            </button>
          </div>

          {loading && <p>Loading products...</p>}

          {error && <p className="error-message">{error}</p>}

          {!loading && !error && products.length === 0 && (
            <p>No products found.</p>
          )}

          {!loading && !error && (
            <div className="product-grid">
              {products.map((product) => (
                <article
                  className="product-card"
                  key={product.id}
                  onClick={() => setSelectedProductId(product.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (
                      event.key === 'Enter' ||
                      event.key === ' '
                    ) {
                      event.preventDefault()
                      setSelectedProductId(product.id)
                    }
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="product-image">🛍️</div>

                  <h3>{product.name}</h3>

                  <p className="product-category">
                    {product.category}
                  </p>

                  <p className="product-description">
                    {product.description}
                  </p>

                  <p className="product-price">
                    ₹{Number(product.price).toLocaleString('en-IN')}
                  </p>

                  <p
                    className={
                      product.stock_quantity > 0
                        ? 'stock available'
                        : 'stock unavailable'
                    }
                  >
                    {product.stock_quantity > 0
                      ? `In Stock (${product.stock_quantity})`
                      : 'Out of Stock'}
                  </p>
                </article>
              ))}
            </div>
          )}

          {!loading && !error && totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage((current) => current - 1)}
                disabled={page === 1}
              >
                Previous
              </button>

              <span>
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage((current) => current + 1)}
                disabled={page === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </section>
      </main>

      <footer>
        <p>© 2026 Vijay Store. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App