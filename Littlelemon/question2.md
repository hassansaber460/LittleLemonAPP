# Question 2 — Customer Menu, Cart, and Order Workflow

## Part A — Customer Registration and Authentication

A new customer can create an account using the registration endpoint:

**Endpoint:** `POST /api/create-new-user/`

**HTTP Method:** `POST`

**Permission:** `AllowAny`, so registration does not require an existing authentication token.

The customer submits a username, email address, and password in the request body.

**Representative request:**

```http
POST /api/create-new-user/
Content-Type: application/json
```

```json
{
    "username": "customer_example",
    "email": "customer@example.com",
    "password": "ExamplePassword123!"
}
```

The `UserSerializer` creates the Django user and uses `set_password()` to hash the password before saving it. It also creates an authentication token for the new user.

After registration, the customer can authenticate using:

**Endpoint:** `POST /api/login/`

**HTTP Method:** `POST`

**Permission:** `AllowAny`

The customer submits their username and password.

```http
POST /api/login/
Content-Type: application/json
```

```json
{
    "username": "customer_example",
    "password": "ExamplePassword123!"
}
```

A successful login returns an authentication token:

```json
{
    "token": "<authentication-token>"
}
```

The customer includes this token in the Authorization header when accessing protected endpoints:

```http
Authorization: Token <authentication-token>
```

The project uses Django REST Framework's `TokenAuthentication` and `SessionAuthentication`. Protected endpoints require an authenticated user.

The application identifies the current customer through `request.user`. For example, the cart and order views use the authenticated user to retrieve or create records belonging to that customer. The customer does not need to submit their own user ID to establish ownership.

---

## Part B — Menu Discovery, Filtering, Sorting, and Pagination

Authenticated customers can browse menu items using:

**Endpoint:** `/api/menu-items/`

**HTTP Method:** `GET`

**Permission:** `IsManagerOrReadOnly`. Authenticated users can retrieve menu items, while only managers can modify them.

### 1. Retrieve all menu items

```http
GET /api/menu-items/
Authorization: Token <authentication-token>
```

The API returns a paginated list of menu items, including their IDs, titles, prices, featured values, and category information.

### 2. Retrieve an individual menu item

```http
GET /api/menu-items/Bruschetta/
Authorization: Token <authentication-token>
```

The detail endpoint retrieves a menu item using its title as the lookup field. A successful request returns the selected item's details. If the item does not exist, the API returns `404 Not Found`.

### 3. Browse categories

Customers can retrieve categories using:

```http
GET /api/categories/
Authorization: Token <authentication-token>
```

They can also retrieve an individual category using:

```http
GET /api/categories/<category-slug>/
Authorization: Token <authentication-token>
```

The category serializer includes hyperlinks to the menu items associated with that category.

### 4. Search and filter menu items

The project uses Django REST Framework's `SearchFilter`.

The configured search fields are:

- `title`
- `category__title`

For example:

```http
GET /api/menu-items/?search=Italian
Authorization: Token <authentication-token>
```

This searches menu item titles and category titles for matching results.

### 5. Sort menu items

The project uses `OrderingFilter`, with `price` and `title` configured as ordering fields.

For example, to sort menu items by price from lowest to highest:

```http
GET /api/menu-items/?ordering=price
Authorization: Token <authentication-token>
```

To sort by price from highest to lowest:

```http
GET /api/menu-items/?ordering=-price
Authorization: Token <authentication-token>
```

### 6. Pagination

The project uses Django REST Framework's `PageNumberPagination`, with a page size of three menu items.

For example:

```http
GET /api/menu-items/?page=2
Authorization: Token <authentication-token>
```

This retrieves the second page of menu items. The paginated response includes navigation information such as `count`, `next`, `previous`, and `results`.

**Representative pagination response:**

```json
{
    "count": 8,
    "next": "http://localhost:8000/api/menu-items/?page=3",
    "previous": "http://localhost:8000/api/menu-items/",
    "results": [
        {
            "id": 4,
            "title": "Example Menu Item",
            "price": "12.00",
            "featured": false,
            "category_read": "http://localhost:8000/api/categories/example/"
        }
    ]
}
```

The exact number of results and URLs depend on the actual database contents and server configuration.

---

## Part C — Customer Cart

An authenticated customer manages their cart through:

**Endpoint:** `/api/cart/menu-items/`

**Permission:** `IsAuthenticated`

The cart is specific to the authenticated user. The view filters cart records using `user=self.request.user`, preventing customers from accessing another user's cart.

### 1. Retrieve the current cart

**HTTP Method:** `GET`

```http
GET /api/cart/menu-items/
Authorization: Token <authentication-token>
```

The API returns the menu items currently stored in the authenticated customer's cart, including their quantities, unit prices, and calculated prices.

### 2. Add an item to the cart

**HTTP Method:** `POST`

The customer submits the menu item ID and quantity. The serializer accepts the menu item through the `menu_item` field.

```http
POST /api/cart/menu-items/
Authorization: Token <authentication-token>
Content-Type: application/json
```

```json
{
    "menu_item": 1,
    "quantity": 2
}
```

The backend handles the remaining values:

- `menu_item`: identifies the selected menu item.
- `quantity`: supplied by the customer.
- `unit_price`: obtained from the menu item's current price.
- `price`: calculated by multiplying unit price by quantity.
- `user`: assigned from the authenticated `request.user`.

The customer cannot submit a different user ID or choose their own unit price or calculated price because those fields are not writable in the serializer.

If the same customer adds an item that already exists in their cart, the implementation increases the existing quantity and refreshes the unit-price snapshot.

**Representative response:**

```json
{
    "id": 1,
    "menu_item": 1,
    "quantity": 2,
    "unit_price": "12.00",
    "price": "24.00"
}
```

### 3. Clear the cart

**HTTP Method:** `DELETE`

```http
DELETE /api/cart/menu-items/
Authorization: Token <authentication-token>
```

The API deletes only the authenticated customer's cart records and returns:

```http
204 No Content
```

This ownership restriction is important because customers must not be able to create or modify cart records on behalf of another user. The backend uses the authenticated identity rather than trusting a user ID supplied by the client.

---

## Part D — Creating and Retrieving Customer Orders

Customers create orders through:

**Endpoint:** `/api/orders/`

**HTTP Method:** `POST`

**Permission:** `IsAuthenticated`

The order creation process is implemented in the `OrderView.create()` method.

### 1. Create an order from the customer's cart

Before placing an order, the customer must have at least one item in their cart.

```http
POST /api/orders/
Authorization: Token <authentication-token>
Content-Type: application/json
```

The API uses the authenticated user to retrieve the customer's cart. The customer does not submit an order owner ID or manually calculate the order total.

The backend performs the following operations:

1. Retrieves the cart items belonging to `request.user`.
2. Checks whether the cart is empty.
3. Calculates the order total using each cart item's unit price and quantity.
4. Creates a new order associated with the authenticated customer.
5. Creates an `OrderItem` record for each cart item.
6. Copies the menu item, quantity, and unit price into the corresponding order item.
7. Calculates and stores each order item's price.
8. Deletes the customer's cart items after successful order creation.

These operations are wrapped in `transaction.atomic()`. This ensures that the order creation and cart-clearing operations are handled as one database transaction.

If the cart is empty, the API returns `400 Bad Request` with an explanatory message.

**Representative successful response:**

```json
{
    "id": 1,
    "user": 5,
    "delivery_crew": null,
    "status": false,
    "date": "2026-11-17",
    "total": "24.00",
    "items": [
        {
            "id": 1,
            "menu_item": 1,
            "quantity": 2,
            "unit_price": "12.00",
            "price": "24.00"
        }
    ]
}
```

The values above are illustrative. Actual IDs, dates, and prices depend on the database.

### 2. Retrieve the customer's order history

**Endpoint:** `/api/orders/`

**HTTP Method:** `GET`

```http
GET /api/orders/
Authorization: Token <authentication-token>
```

The API checks the user's role. A customer who is neither a Manager nor a Delivery Crew member receives only orders where:

```python
Order.objects.filter(user=request.user)
```

This ensures that customers can view their own order history without seeing other customers' orders.

### 3. Retrieve an individual order

**Endpoint:** `/api/orders/<orderId>/`

**HTTP Method:** `GET`

For example:

```http
GET /api/orders/1/
Authorization: Token <authentication-token>
```

The `SingleOrderView` uses a role-based queryset to restrict which orders the current user can access.

A customer can retrieve an order only if that order belongs to them. If they attempt to retrieve an order belonging to another customer, the filtered queryset does not contain that order, and the API returns `404 Not Found`.

Customers are also prevented from modifying orders. An attempt to update an order as a customer returns `403 Forbidden`.

---

## How the Customer API Workflow Works Together

The Little Lemon API provides a complete customer journey through connected authentication, menu, cart, and order endpoints.

First, a customer registers and logs in to obtain an authentication token. The token is then used to access protected endpoints. The customer browses menu items and categories, searches for items, sorts results by price or title, and navigates through paginated results. Next, the customer adds selected menu items to their cart. The backend assigns cart ownership, retrieves the actual menu prices, and calculates item totals. Finally, the customer places an order. The API converts the cart items into order items, calculates the order total, clears the cart, and allows the customer to retrieve their own order history and individual orders.

By using authentication, serializers, permissions, ownership-based querysets, and database transactions, the API protects customer data and provides a structured restaurant ordering workflow.