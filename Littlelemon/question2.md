## Question 2: Customer Features

### 1. Customer Registration and Login

Customers can register using:

`POST /api/create-new-user/`

Example request:

```json
{
    "username": "customer1",
    "email": "customer@example.com",
    "password": "StrongPassword123"
}
```

Customers can authenticate using:

`POST /api/login/`

Example request:

```json
{
    "username": "customer1",
    "password": "StrongPassword123"
}
```

The login endpoint returns an authentication token that can be used in subsequent API requests.

### 2. Browse the Menu

Customers can retrieve menu categories and menu items:

- `GET /api/categories/`
- `GET /api/menu-items/`
- `GET /api/menu-items/{title}/`

The API uses Django REST Framework serializers to convert model instances into JSON responses.

### 3. Shopping Cart

Customers can manage their cart through:

`/api/cart/menu-items/`

Supported operations:

- `GET` – Retrieves the authenticated user's cart.
- `POST` – Adds an item to the cart.
- `DELETE` – Clears the authenticated user's cart.

The `Cart` model stores the user, menu item, quantity, unit price, and calculated price.

A uniqueness constraint prevents the same menu item from being added more than once for the same user.

### 4. Create Orders

Customers can create an order using:

`POST /api/orders/`

The intended workflow is:

1. Retrieve the customer's cart items.
2. Calculate the order total.
3. Create an order associated with the authenticated customer.
4. Create the corresponding order items.
5. Clear the customer's cart.

### 5. View Order History

Customers can retrieve their orders using:

`GET /api/orders/`

The queryset is filtered to return orders belonging to the authenticated customer.

Customers can also retrieve an individual order using:

`GET /api/orders/{id}/`

### 6. Pagination

The project configures Django REST Framework's `PageNumberPagination` with a page size of three records.

This allows API responses to return results in smaller pages rather than returning all records at once.

## Conclusion

The Little Lemon API uses Django REST Framework, Django authentication, token-based authentication, serializers, models, and custom permissions to implement a restaurant ordering system.

The application separates responsibilities between administrators, managers, delivery crew members, and customers. Its main features include user management, menu management, cart operations, and order processing.