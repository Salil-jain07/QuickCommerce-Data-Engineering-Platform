
# QuickCommerce Data Model

## 1. Customers
- customer_id (Primary Key)
- customer_name
- email
- phone
- city
- state
- signup_date

## 2. Products
- product_id (Primary Key)
- product_name
- category
- brand
- mrp
- unit

## 3. Stores
- store_id (Primary Key)
- platform
- city
- latitude
- longitude
- opening_date

## 4. Orders
- order_id (Primary Key)
- customer_id (Foreign Key)
- store_id (Foreign Key)
- order_date
- order_time
- platform
- order_status
- payment_method
- order_total

## 5. Order Items
- order_item_id (Primary Key)
- order_id (Foreign Key)
- product_id (Foreign Key)
- quantity
- selling_price
- item_total

## 6. Payments
- payment_id (Primary Key)
- order_id (Foreign Key)
- payment_method
- payment_amount
- payment_status
- payment_timestamp

## 7. Deliveries
- delivery_id (Primary Key)
- order_id (Foreign Key)
- partner_id
- pickup_time
- promised_delivery_time
- actual_delivery_time
- delivery_duration
- delivery_status
- delay_reason

## Relationships
- One customer can place multiple orders.
- One store can process multiple orders.
- One order can contain multiple order items.
- One product can appear in multiple order items.
- Each order has one payment record.
- Each order has one delivery record.
