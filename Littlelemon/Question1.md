# Little Lemon REST API – Authentication, Permissions, Menu Management, and Order Workflow

## 1. Authentication and Role-Based Authorization

The Little Lemon API uses Django REST Framework Token Authentication to identify users and protect API endpoints.

Users can register through:

`POST /api/create-new-user/`

Example request:

```json
{
    "username": "customer1",
    "email": "customer@example.com",
    "password": "SecurePassword123"
}
```

The registration serializer securely hashes the password using Django's `set_password()` method and creates an authentication token for the new user.

Users can log in through:

`POST /api/login/`

Example request:

```json
{
    "username": "customer1",
    "password": "SecurePassword123"
}
```

A successful login returns:

```json
{
    "token": "generated-authentication-token"
}
```

The API also supports the standard DRF token endpoint:

`POST /api-token-auth/`

For authenticated requests, clients include the token in the HTTP Authorization header:

```http
Authorization: Token generated-authentication-token
```

The API distinguishes authentication from authorization:

- Authentication verifies the identity of the user through a valid token.
- Authorization determines which operations that authenticated user is allowed to perform.

The application uses Django's built-in User and Group models to implement role-based access control.

The main roles are:

| Role | Responsibilities |
|---|---|
| Administrator | Administrative operations and Manager group membership management |
| Manager | Menu management, group management for delivery crew, order management, and delivery assignment |
| Delivery Crew | Access assigned orders and update their delivery status |
| Customer | Browse the menu, manage their cart, create orders, and access their own orders |

Users who are not members of the Manager or Delivery Crew groups are treated as customers by the application.

Custom permission classes such as `IsManager`, `IsManagerOrReadOnly`, and `IsManagerOrDeliveryCrew` enforce these restrictions.

## 2. User Group Management

The API uses Django Groups to assign roles without creating separate user models.

### Manager group

Endpoint:

`/api/groups/manager/users`

Supported methods:

- GET: List users belonging to the Manager group.
- POST: Add an existing user to the Manager group.
- DELETE: Remove a user from the Manager group.

These operations are restricted to administrators through DRF's `IsAdminUser` permission.

Example request:

```http
POST /api/groups/manager/users
Authorization: Token ADMIN_TOKEN
Content-Type: application/json
```

```json
{
    "username": "new_manager"
}
```

Example response:

```json
{
    "detail": "new_manager added to Manager."
}
```

### Delivery Crew group

Endpoint:

`/api/groups/delivery-crew/users`

Supported methods:

- GET: List Delivery Crew members.
- POST: Add an existing user to the Delivery Crew group.
- DELETE: Remove a user from the Delivery Crew group.

Only authorized Managers can perform these operations.

Example request:

```http
POST /api/groups/delivery-crew/users
Authorization: Token MANAGER_TOKEN
Content-Type: application/json
```

```json
{
    "username": "delivery_user"
}
```

Example response:

```json
{
    "detail": "delivery_user added to Delivery Crew."
}
```

Unauthorized users cannot manage group membership. Requests without valid authentication are rejected, while authenticated users without the required permissions receive HTTP 403 Forbidden.

## 3. Menu Management

The Menu API allows authenticated users to retrieve menu information while restricting modifications to Managers.

### Menu endpoints

| Endpoint | HTTP method | Access |
|---|---|---|
| `/api/menu-items/` | GET | Authenticated users |
| `/api/menu-items/` | POST | Managers |
| `/api/menu-items/<title>/` | GET | Authenticated users |
| `/api/menu-items/<title>/` | PUT | Managers |
| `/api/menu-items/<title>/` | PATCH | Managers |
| `/api/menu-items/<title>/` | DELETE | Managers |

The `IsManagerOrReadOnly` permission class allows safe HTTP methods such as GET for authenticated users but requires Manager privileges for modification requests.

A MenuItem contains fields such as:

- `title`: Menu item name.
- `price`: Menu item price.
- `featured`: Indicates whether the item is featured.
- `category`: Foreign key relationship to Category.

The `featured` field allows Managers to highlight selected menu items without changing their category or other menu information.

Example: A Manager creates a featured menu item.

```http
POST /api/menu-items/
Authorization: Token MANAGER_TOKEN
Content-Type: application/json
```

```json
{
    "title": "Greek Salad",
    "price": "12.50",
    "featured": true,
    "category_write": 1
}
```

A Manager can also update the featured status independently:

```http
PATCH /api/menu-items/Greek Salad/
Authorization: Token MANAGER_TOKEN
Content-Type: application/json
```

```json
{
    "featured": false
}
```

Customers and Delivery Crew members can retrieve menu items but cannot create, modify, or delete them. Such unauthorized modification attempts return HTTP 403 Forbidden.

## 4. Manager and Delivery Crew Order Workflow

The order workflow connects customer purchases with Manager order administration and Delivery Crew fulfillment.

### Customer order creation

Customers add menu items to their personal cart through:

`/api/cart/menu-items/`

Supported methods:

- GET: Retrieve the authenticated user's cart.
- POST: Add a menu item to the cart.
- DELETE: Clear the authenticated user's cart.

The API calculates prices using the actual menu item price stored in the database rather than trusting client-submitted prices.

Customers create orders through:

`POST /api/orders/`

The API:

1. Retrieves the authenticated customer's cart items.
2. Calculates the order total.
3. Creates the Order record.
4. Creates the related OrderItem records.
5. Clears the customer's cart.

These database operations are executed within `transaction.atomic()` to maintain data consistency.

### Manager order management and assignment

Managers can retrieve all orders through:

`GET /api/orders/`

Managers can assign an order to an existing Delivery Crew member using:

`PATCH /api/orders/<order_id>/`

Example:

```http
PATCH /api/orders/1/
Authorization: Token MANAGER_TOKEN
Content-Type: application/json
```

```json
{
    "delivery_crew": 5
}
```

The serializer validates that the selected user belongs to the Delivery Crew group. A user who is not a Delivery Crew member cannot be assigned.

Managers can also update permitted order fields and oversee the order fulfillment process.

### Delivery Crew order retrieval

Delivery Crew members retrieve their assigned orders through:

`GET /api/orders/`

The queryset is filtered by the authenticated delivery crew member:

`Order.objects.filter(delivery_crew=request.user)`

This ensures that each delivery crew member can only retrieve orders assigned to them.

They cannot access another crew member's orders.

### Delivery status updates

Delivery Crew members can update the status of their assigned orders using:

`PATCH /api/orders/<order_id>/`

Example:

```http
PATCH /api/orders/1/
Authorization: Token DELIVERY_CREW_TOKEN
Content-Type: application/json
```

```json
{
    "status": true
}
```

The Boolean status field represents the order's fulfillment state:

- `false`: The order has not yet been marked as delivered.
- `true`: The order has been marked as delivered.

The delivery crew member is restricted to updating the `status` field only. They cannot modify the customer, order total, assigned delivery crew member, or order items.

Customers cannot update orders, and delivery crew members cannot retrieve or modify orders that are not assigned to them.

## 5. Security, Authorization, and Error Handling

Authentication alone is not sufficient to protect an API. A valid token proves the user's identity, but it does not grant permission to perform every operation.

For this reason, the application combines:

- Token Authentication to identify users.
- Django Groups to organize users by role.
- Custom DRF permission classes to restrict operations.
- Queryset filtering to enforce object-level access restrictions.
- Serializer validation to prevent unauthorized field changes.
- Database transactions to protect order creation consistency.

The API uses appropriate HTTP status codes:

| Status | Meaning |
|---|---|
| 200 OK | Successful retrieval or update |
| 201 Created | Successful registration or resource creation |
| 204 No Content | Successful deletion |
| 400 Bad Request | Invalid input or disallowed field update |
| 401 Unauthorized | Missing or invalid authentication credentials |
| 403 Forbidden | Authenticated user lacks the required permission |
| 404 Not Found | Requested object does not exist or is outside the user's accessible queryset |

## Conclusion

The Little Lemon API combines Django Token Authentication, Django Groups, custom DRF permissions, serializer validation, and user-specific querysets to implement a role-based restaurant management system.

Customers can manage their carts and orders, Managers can manage menu items and oversee order fulfillment, and Delivery Crew members can access only their assigned orders and update their delivery status.

This separation of responsibilities ensures that authentication, authorization, menu management, group management, and order fulfillment work together as part of a secure REST API architecture.