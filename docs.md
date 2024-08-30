# API Documentation

## Authentication and User Management APIs

### 1. **Register User**
## **Base URL:** "http://127.0.0.1:8000/api"
   - **URL:** `/register/`
   - **Method:** `POST`
   - **Description:** Registers a new user. If the role is `OPERATOR`, also creates a corresponding `BusOperator` and allows image uploads for the operator.
   - **Request Payload:**
     ```json
     {
       "phone_number": "+237XXXXXXXXX",
       "password": "yourpassword",
       "first_name": "John",
       "last_name": "Doe",
       "email": "johndoe@example.com",
       "role": "OPERATOR",  # Or "CUSTOMER", "ADMIN"
       "business_name": "Bus Operator Ltd.", // needed when role is operator
       "business_description": "Best bus operator in town.", // needed when role is operator
       "business_contact": "+237XXXXXXXXX", // needed when role is operator
       "business_email": "operator@example.com" // needed when role is operator
     }
     ```
   - **Request Files (Optional for OPERATOR):**
     - `images[]`: List of images for the bus operator.
   - **Response:**
     - **201 Created:** 
       ```json
       {
         "refresh": "your_refresh_token",
         "access": "your_access_token"
       }
       ```
     - **400 Bad Request:** Invalid input data.
     - **500 Internal Server Error:** Server-side error.
     
### 2. **Login User**
   - **URL:** `/login/`
   - **Method:** `POST`
   - **Description:** Authenticates a user with phone number and password.
   - **Request Payload:**
     ```json
     {
       "phone_number": "+237XXXXXXXXX",
       "password": "yourpassword"
     }
     ```
   - **Response:**
     - **200 OK:** 
       ```json
       {
         "refresh": "your_refresh_token",
         "access": "your_access_token"
       }
       ```
     - **400 Bad Request:** Invalid phone number or password.

### 3. **Logout User**
   - **URL:** `/logout/`
   - **Method:** `POST`
   - **Description:** Logs out the authenticated user.
   - **Request:** 
     - No payload required.
   - **Response:**
     - **200 OK:** 
       ```json
       {
         "message": "Successfully logged out."
       }
       ```
     - **500 Internal Server Error:** Server-side error.

### 4. **Edit Bus Operator Profile**
   - **URL:** `/edit-profile/`
   - **Method:** `POST`
   - **Description:** Allows an `OPERATOR` to edit their profile.
   - **Request Payload (Partial Updates Allowed):**
     ```json
     {
       "name": "Updated Bus Operator Ltd.", // optional
       "description": "Updated description.", // optional
       "contact": "+237XXXXXXXXX", // optional
       "email": "newoperator@example.com" // optional
     }
     ```
   - **Response:**
     - **200 OK:** 
       ```json
       {
         "message": "Profile successfully updated.",
         "data": {
           "id": 1,
           "user": 1,
           "name": "Updated Bus Operator Ltd.",
           "description": "Updated description.",
           "contact": "+237XXXXXXXXX",
           "email": "newoperator@example.com",
           "created_at": "2024-08-30T12:34:56Z"
         }
       }
       ```
     - **400 Bad Request:** No corresponding `BusOperator` found for the user or invalid data.
     - **403 Forbidden:** User is not authorized to edit the profile.

### 5. **Change Password**
   - **URL:** `/change-password/`
   - **Method:** `POST`
   - **Description:** Allows an authenticated user to change their password.
   - **Request Payload:**
     ```json
     {
       "password": "newpassword"
     }
     ```
   - **Response:**
     - **200 OK:** 
       ```json
       {
         "message": "Password successfully updated.",
         "data": {
           "id": 1,
           "password": "**********"
         }
       }
       ```
     - **400 Bad Request:** Invalid data (e.g., password too short).
     - **500 Internal Server Error:** Server-side error.

## Bus Management APIs

### 1. **Create Bus**
   - **URL:** `/create-bus/`
   - **Method:** `POST`
   - **Description:** Creates a new bus in the system.
   - **Request Payload:**
     ```json
     {
       "name": "Bus Name",
       "capacity": 50,
       "operator_id": 1
     }
     ```
   - **Response:**
     - **201 Created:** Bus created successfully.
     - **400 Bad Request:** Invalid data.

### 2. **Create Schedule**
   - **URL:** `/create-schedule/`
   - **Method:** `POST`
   - **Description:** Creates a new schedule for a bus.
   - **Request Payload:**
     ```json
     {
       "bus_id": 1,
       "departure_time": "2024-09-01T08:00:00Z",
       "arrival_time": "2024-09-01T12:00:00Z",
       "origin": "City A",
       "destination": "City B"
     }
     ```
   - **Response:**
     - **201 Created:** Schedule created successfully.
     - **400 Bad Request:** Invalid data.

### 3. **Get Buses**
   - **URL:** `/buses/`
   - **Method:** `GET`
   - **Description:** Retrieves a list of all buses.
   - **Response:**
     - **200 OK:** 
       ```json
       [
         {
           "id": 1,
           "name": "Bus Name",
           "capacity": 50,
           "operator": "Operator Name"
         },
         ...
       ]
       ```
     - **500 Internal Server Error:** Server-side error.

### 4. **Bus Detail**
   - **URL:** `/bus-detail/<id>/`
   - **Method:** `GET`
   - **Description:** Retrieves details of a specific bus by its ID.
   - **Response:**
     - **200 OK:** 
       ```json
       {
         "id": 1,
         "name": "Bus Name",
         "capacity": 50,
         "operator": "Operator Name",
         "schedules": [
           {
             "id": 1,
             "departure_time": "2024-09-01T08:00:00Z",
             "arrival_time": "2024-09-01T12:00:00Z",
             "origin": "City A",
             "destination": "City B"
           }
           ...
         ]
       }
       ```
     - **404 Not Found:** Bus with the specified ID does not exist.
     - **500 Internal Server Error:** Server-side error.

### 5. **Book a Bus**
   - **URL:** `/book/`
   - **Method:** `POST`
   - **Description:** Books a seat on a bus.
   - **Request Payload:**
     ```json
     {
       "bus": {
        "id": 1
       },
       "schedule_id": 1,
       "user_id": 1,
       "seat_number": 12
     }
     ```
   - **Response:**
     - **201 Created:** Booking created successfully.
     - **400 Bad Request:** Invalid data.

### 6. **Pay for Booking**
   - **URL:** `/pay/`
   - **Method:** `POST`
   - **Description:** Processes payment for a bus booking.
   - **Request Payload:**
     ```json
     {
       "booking_id": 1,
       "amount": 10000,
       "currency": "XAF",
       "phone_number": "+237XXXXXXXXX"
     }
     ```
   - **Response:**
     - **200 OK:** Payment processed successfully.
     - **400 Bad Request:** Invalid data.
     - **500 Internal Server Error:** Server-side error.
