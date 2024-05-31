import snowflake.connector
from flask import jsonify
import datetime

class SnowflakeDB:
    def __init__(self, config):
        self.config = config

    def get_connection(self):
        try:
            return snowflake.connector.connect(**self.config)
        except snowflake.connector.Error as e:
            error_message = str(e)
            if "Your user account has been temporarily locked" in error_message:
                return jsonify({
                    "error": "Your user account has been temporarily locked due to too many failed attempts. Try again after 15 minutes or contact your account administrator for assistance.",
                    "details": error_message
                }), 403
            return jsonify({"error": error_message}), 500

    def get_product_details_with_location(self, search_term):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if isinstance(connection, tuple):
                # Return the error response directly if get_connection returns an error
                return connection

            cursor = connection.cursor()
            search_term = '%{}%'.format(search_term)

            # Command to get product details
            cursor.execute("""
                SELECT p.* 
                FROM PRODUCT p 
                WHERE p.PRODUCT_NAME LIKE %s
            """, (search_term,))
            products = cursor.fetchall()
            product_column_names = [desc[0].lower() for desc in cursor.description]
            products_list = [dict(zip(product_column_names, product)) for product in products]

            # Command to get product location details
            cursor.execute("""
                SELECT DISTINCT I.* 
                FROM PRODUCT P 
                INNER JOIN LOCATIONS I ON p.LOCATION_ID = I.LOCATION_ID 
                WHERE p.PRODUCT_NAME LIKE %s
            """, (search_term,))
            locations = cursor.fetchall()
            location_column_names = [desc[0].lower() for desc in cursor.description]
            location_list = [dict(zip(location_column_names, location)) for location in locations]

            # Formatting response
            response = {
                'products': products_list,
                'locations': location_list,
            }

            # Getting shortcut details
            if products_list and location_list:
                product_name = products_list[0]['product_name']
                location_details = location_list[0]
                location_zone = location_details.get('zone', 'N/A')
                location_aisle = location_details.get('aisle', 'N/A')
                location_shelf = location_details.get('shelf', 'N/A')
                location_bin = location_details.get('bin', 'N/A')

                location_description = (
                    f'Quick instruction to locate "{product_name}": Go to the {location_zone} Zone, '
                    f'find aisle {location_aisle}, locate shelf {location_shelf}, and look for bin {location_bin}. '
                    f'Collect the product "{product_name}" from bin {location_bin}.'
                )
                response['location'] = location_description

            return jsonify(response)

        except snowflake.connector.Error as e:
            return jsonify({"error": str(e)})

        finally:
            if cursor:
                cursor.close()
            if connection and not isinstance(connection, tuple):
                connection.close()

    def delete_expired_products(self):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if isinstance(connection, tuple):
                # Return the error response directly if get_connection returns an error
                return connection
            
            cursor = connection.cursor()
            current_date = datetime.datetime.now().date()
            cursor.execute("DELETE FROM PRODUCT WHERE EXPIRY_DATE < %s", (current_date,))
            connection.commit()
            print("Products deleted successfully.")
        except snowflake.connector.Error as e:
            print(f"Error while deleting products: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if connection and not isinstance(connection, tuple):
                connection.close()

    def display_products_details(self):
        connection = None
        cursor = None
        try:
            self.delete_expired_products()
            connection = self.get_connection()
            if isinstance(connection, tuple):
                # Return the error response directly if get_connection returns an error
                return connection

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM PRODUCT")
            products = cursor.fetchall()
            column_names = [desc[0].lower() for desc in cursor.description]
            products_list = [dict(zip(column_names, product)) for product in products]
            return jsonify(products_list)
        except snowflake.connector.Error as e:
            return jsonify({'error': str(e)})
        finally:
            if cursor:
                cursor.close()
            if connection and not isinstance(connection, tuple):
                connection.close()

    def insert_data(self, data):
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            # Extracting data from the input
            purchase_id = data.get('purchase_id')
            supplier_id = data.get('supplier_id')
            supplier_name = data.get('supplier_name', 'Unknown Supplier')
            product_name = data.get('product_name')
            description = data.get('description', '')
            num_products_received = data.get('num_products_received')
            date_of_purchase = data.get('date_of_purchase', '2000-01-01 00:00:00')
            category = data.get('category', 'General')
            unit_cost = data.get('unit_cost', 0)
            selling_price = data.get('selling_price', 0)
            reorder_level = data.get('reorder_level', 0)
            expiry_date = data.get('expiry_date')
            location_id = data.get('location_id')
            location_aisle = data.get('location_aisle')
            location_shelf = data.get('location_shelf')
            location_bin = data.get('location_bin')
            location_zone = data.get('location_zone')

            # Check for required fields
            required_fields = [purchase_id, supplier_id, product_name, num_products_received, date_of_purchase, unit_cost, reorder_level]
            if None in required_fields:
                return jsonify({"error": "Missing required fields or fields cannot be NULL"}), 400

            # Check if the product already exists
            cursor.execute("SELECT * FROM PRODUCT WHERE PRODUCT_NAME = %s", (product_name,))
            product = cursor.fetchone()

            if product:
                # If product exists, update the quantity and reorder level
                column_names = [desc[0].lower() for desc in cursor.description]
                product_dict = dict(zip(column_names, product))
                
                new_quantity = product_dict.get('quantity_available', 0) + num_products_received
                new_reorder_level = max(0, product_dict.get('reorder_level', 0) - num_products_received)
                
                cursor.execute("""
                    UPDATE PRODUCT
                    SET QUANTITY_AVAILABLE = %s, REORDER_LEVEL = %s, UNIT_COST = %s
                    WHERE PRODUCT_NAME = %s
                """, (new_quantity, new_reorder_level, unit_cost, product_name))
            else:
                # If product does not exist, insert a new product
                cursor.execute("""
                    INSERT INTO PRODUCT (
                        SUPPLIER_ID, SUPPLIER_NAME, PRODUCT_NAME, DESCRIPTION, NUMBER_OF_PRODUCT_PURCHASED,
                        DATE_OF_PURCHASE, CATEGORY, QUANTITY_AVAILABLE, UNIT_COST, SELLING_PRICE,
                        REORDER_LEVEL, EXPIRY_DATE, LOCATION_ID
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    supplier_id, supplier_name, product_name, description, num_products_received,
                    date_of_purchase, category, num_products_received, unit_cost, selling_price,
                    reorder_level, expiry_date, location_id
                ))

            # Insert into PURCHASES
            cursor.execute("""
                INSERT INTO PURCHASES (PURCHASEID, SUPPLIERID, DATEOFPURCHASE, NUMOFPRODUCTSRECEIVED, PRODUCT_NAME, CATEGORY)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (purchase_id, supplier_id, date_of_purchase, num_products_received, product_name, category))

            # Insert into SUPPLIERS
            cursor.execute("""
                INSERT INTO SUPPLIERS (SUPPLIERID, SUPPLIERNAME, PRODUCT_NAME, CATEGORY, DELIVERY_DATE, DELIVERY_QUANTITY)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (supplier_id, supplier_name, product_name, category, date_of_purchase, num_products_received))

            # Insert into LOCATIONS
            cursor.execute("""
                INSERT INTO LOCATIONS (LOCATION_ID, AISLE, SHELF, BIN, ZONE)
                VALUES (%s, %s, %s, %s, %s)
            """, (location_id, location_aisle, location_shelf, location_bin, location_zone))
            
            connection.commit()
            return jsonify({"message": "Data inserted successfully"}), 201
        except snowflake.connector.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()

    def order_service_details(self, data):
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            order_id = data.get('order_id')
            product_name = data.get('product_name')
            number_shipped = data.get('number_shipped')
            order_date = data.get('order_date')

            if not order_id or not product_name or not number_shipped or not order_date:
                return jsonify({"error": "Missing required fields"}), 400
            
            cursor.execute("SELECT QUANTITY_AVAILABLE FROM PRODUCT WHERE PRODUCT_NAME = %s", (product_name,))
            product = cursor.fetchone()
            if not product:
                return jsonify({"error": f"Product {product_name} not found"}), 404
            
            current_quantity = product[0]

            if current_quantity < number_shipped:
                return jsonify({'error': f'Not enough quantity for product {product_name}'}), 404

            new_quantity = current_quantity - number_shipped

            cursor.execute("UPDATE PRODUCT SET QUANTITY_AVAILABLE = %s WHERE PRODUCT_NAME = %s", (new_quantity, product_name))

            cursor.execute("""
                INSERT INTO ORDERS (ORDERID, PRODUCTNAME, NUMBERSHIPPED, ORDERDATE) 
                VALUES (%s, %s, %s, %s)
            """, (order_id, product_name, number_shipped, order_date))
            
            connection.commit()
            return jsonify({'message': 'Order placed and product quantity updated successfully'})
        except snowflake.connector.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
