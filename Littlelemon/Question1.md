# Little Lemon REST API – Assignment

## Question 1: Authentication, Authorization, and Management

The Little Lemon API is developed using Django and Django REST Framework. It uses Django's built-in User and Group models to manage authentication and role-based access control.

### 1. User Authentication

The API provides endpoints for user registration and login:

- `POST /api/create-new-user/` – Creates a new user.
- `POST /api/login/` – Authenticates a user and returns an authentication token.
- `POST /api-token-auth/` – Provides token authentication using Django REST Framework's built-in token endpoint.

Passwords are securely hashed using Django's `set_password()` method. The API uses Token Authentication and Session Authentication.

Authenticated requests can include the token in the HTTP header:

`Authorization: Token <your_token>`

### 2. User Roles and Groups

The project uses Django Groups to organize users into roles:

- Administrators: Django superusers with administrative privileges.
- Managers: Users belonging to the `Manager` group.
- Delivery Crew: Users belonging to the `Delivery Crew` group.
- Customers: Regular registered users.

The API includes group-management endpoints:

- `GET /api/groups/manager/users` – Lists manager users.
- `POST /api/groups/manager/users` – Adds a user to the Manager group.
- `DELETE /api/groups/manager/users` – Removes a user from the Manager group.
- `GET /api/groups/delivery-crew/users` – Lists delivery crew users.
- `POST /api/groups/delivery-crew/users` – Adds a user to the Delivery Crew group.
- `DELETE /api/groups/delivery-crew/users` – Removes a user from the Delivery Crew group.

The project implements custom permission classes to identify managers and delivery crew members.

### 3. Menu Management

The menu functionality is implemented using the `Category` and `MenuItem` models.

Available endpoints:

- `GET /api/categories/` – Retrieves menu categories.
- `POST /api/categories/` – Creates a category.
- `GET /api/categories/{slug}/` – Retrieves a specific category.
- `GET /api/menu-items/` – Lists menu items.
- `POST /api/menu-items/` – Creates a menu item.
- `GET /api/menu-items/{title}/` – Retrieves a specific menu item.

The `IsManagerOrReadOnly` permission class is used to restrict menu-item creation to managers while allowing authenticated users to read menu items.

### 4. Order and Delivery Management

The project includes `Order` and `OrderItem` models.

An order stores the customer, assigned delivery crew member, order status, total amount, and creation date.

Available endpoints:

- `GET /api/orders/` – Lists orders according to the current user's role.
- `POST /api/orders/` – Creates an order from cart items.
- `GET /api/orders/{id}/` – Retrieves order details.
- `PATCH /api/orders/{id}/` – Updates an order.

The order list is filtered according to the user:

- Administrators can view all orders.
- Customers can view their own orders.
- Delivery crew members can view orders assigned to them.

The order status is represented by a Boolean field.