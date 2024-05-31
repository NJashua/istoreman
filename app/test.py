# # import snowflake.connector
# # from flask import Flask, jsonify, request

# # app = Flask(__name__)

# # snowflake_config = {
# #     'user': 'Nithin',
# #     'password': 'Nithin@2024',
# #     'account': 'bdhriyc-ke24872',
# #     'database': 'INVENTORY',
# #     'schema': 'PUBLIC'
# # }

# # def get_connection():
# #     connection = snowflake.connector.connect(**snowflake_config)
# #     return connection

# # def display_products_details():
# #     try:
# #         conn = get_connection()
# #         cursor = conn.cursor()
# #         cursor.execute("SELECT * FROM PRODUCT")
# #         products = cursor.fetchall()
# #         column_names = [desc[0] for desc in cursor.description]
# #         products_list = [dict(zip(column_names, product)) for product in products]
# #         return jsonify(products_list)
# #     except snowflake.connector.Error as e:
# #         return jsonify({'error': str(e)})
# #     finally:
# #         cursor.close()
# #         conn.close()

# # def insert_data(data):
# #     try:
# #         connection = get_connection()
# #         cursor = connection.cursor()

# #         purchase_id = data.get('purchase_id')
# #         supplier_id = data.get('supplier_id')
# #         supplier_name = data.get('supplier_name', 'Unknown Supplier')
# #         product_name = data.get('product_name')
# #         description = data.get('description', '')
# #         num_products_received = data.get('num_products_received', 0)
# #         date_of_purchase = data.get('date_of_purchase', '2000-01-01 00:00:00')
# #         category = data.get('category', 'General')
# #         quantity_available = data.get('quantity_available', 0)
# #         unit_cost = data.get('unit_cost', 0)
# #         selling_price = data.get('selling_price', 0)
# #         reorder_level = data.get('reorder_level', 0)

# #         # Check for required fields
# #         if None in [purchase_id, supplier_id, product_name, num_products_received, date_of_purchase, unit_cost, reorder_level]:
# #             return jsonify({"error": "Missing required fields or fields cannot be NULL"}), 400

# #         cursor.execute("SELECT * FROM PRODUCT WHERE PRODUCT_NAME = %s", (product_name,))
# #         product = cursor.fetchone()

# #         if product:
# #             column_names = [desc[0] for desc in cursor.description]
# #             product_dict = dict(zip(column_names, product))
# #             new_quantity = product_dict['QUANTITY_AVAILABLE'] + num_products_received
# #             new_reorder_level = max(0, product_dict['REORDER_LEVEL'] - num_products_received)
# #             cursor.execute("""
# #                 UPDATE PRODUCT
# #                 SET QUANTITY_AVAILABLE = %s, REORDER_LEVEL = %s, UNIT_COST = %s
# #                 WHERE PRODUCT_NAME = %s
# #             """, (new_quantity, new_reorder_level, unit_cost, product_name))
# #         else:
# #             cursor.execute("""
# #                 INSERT INTO PRODUCT (SUPPLIER_ID, SUPPLIER_NAME, PRODUCT_NAME, DESCRIPTION, NUMBER_OF_PRODUCT_PURCHASED, DATE_OF_PURCHASE, CATEGORY, QUANTITY_AVAILABLE, UNIT_COST, SELLING_PRICE, REORDER_LEVEL)
# #                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
# #             """, (supplier_id, supplier_name, product_name, description, num_products_received, date_of_purchase, category, num_products_received, unit_cost, selling_price, reorder_level))

# #         cursor.execute("""
# #             INSERT INTO PURCHASES (PURCHASEID, SUPPLIERID, DATEOFPURCHASE, NUMOFPRODUCTSRECEIVED, PRODUCT_NAME, CATEGORY)
# #             VALUES (%s, %s, %s, %s, %s, %s)
# #         """, (purchase_id, supplier_id, date_of_purchase, num_products_received, product_name, category))

# #         cursor.execute("""
# #             INSERT INTO SUPPLIERS (SUPPLIERID, SUPPLIERNAME, PRODUCT_NAME, CATEGORY, DELIVERY_DATE, DELIVERY_QUANTITY)
# #             VALUES (%s, %s, %s, %s, %s, %s)
# #         """, (supplier_id, supplier_name, product_name, category, date_of_purchase, num_products_received))

# #         connection.commit()
# #         return jsonify({"message": "Data inserted successfully"})
# #     except snowflake.connector.Error as e:
# #         return jsonify({'error': str(e)})
# #     finally:
# #         cursor.close()
# #         connection.close()

# # @app.route('/display_products', methods=['GET'])
# # def display_products():
# #     return display_products_details()

# # @app.route('/purchase_product', methods=['POST'])
# # def insert():
# #     data = request.get_json()
# #     return insert_data(data)



# # if __name__ == '__main__':
# #     app.run(debug=True)




# import uuid
# import snowflake.connector
# from flask import jsonify

# class SnowflakeDB:
#     def __init__(self, config):
#         self.config = config

#     def get_connection(self):
#         connection = snowflake.connector.connect(**self.config)
#         return connection

#     def order_service_details(self, data):
#         try:
#             connection = self.get_connection()
#             cursor = connection.cursor()

#             product_name = data.get('product_name')
#             number_shipped = data.get('number_shipped')
#             order_date = data.get('order_date')

#             if not product_name or not number_shipped or not order_date:
#                 return jsonify({"error": "Missing required fields"}), 400

#             # Fetch the current quantity available for the product
#             cursor.execute("SELECT PRODUCTID, QUANTITY_AVAILABLE FROM PRODUCT WHERE PRODUCT_NAME = %s", (product_name,))
#             product = cursor.fetchone()
#             if not product:
#                 return jsonify({"error": f"Product {product_name} not found"}), 404

#             product_id, current_quantity = product

#             # Check if there is enough quantity to fulfill the order
#             if current_quantity < number_shipped:
#                 return jsonify({"error": f"Not enough quantity for product {product_name}"}), 400

#             # Decrement the quantity available
#             new_quantity = current_quantity - number_shipped

#             # Update the PRODUCT table
#             cursor.execute("""
#                 UPDATE PRODUCT
#                 SET QUANTITY_AVAILABLE = %s
#                 WHERE PRODUCTID = %s
#             """, (new_quantity, product_id))

#             # Insert order details into ORDERS table
#             order_id = str(uuid.uuid4())
#             cursor.execute("""
#                 INSERT INTO ORDERS (ORDERID, PRODUCTID, PRODUCTNAME, NUMBERSHIPPED, ORDERDATE)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (order_id, product_id, product_name, number_shipped, order_date))

#             connection.commit()
#             return jsonify({"message": "Order placed and product quantity updated successfully"})
#         except snowflake.connector.Error as e:
#             return jsonify({'error': str(e)})
#         finally:
#             cursor.close()
#             connection.close()

#     def display_products_details(self):
#         try:
#             conn = self.get_connection()
#             cursor = conn.cursor()
#             cursor.execute("SELECT * FROM PRODUCT")
#             products = cursor.fetchall()
#             column_names = [desc[0] for desc in cursor.description]
#             products_list = [dict(zip(column_names, product)) for product in products]
#             return jsonify(products_list)
#         except snowflake.connector.Error as e:
#             return jsonify({'error': str(e)})
#         finally:
#             cursor.close()
#             conn.close()










# def order_service_details(self, data):
#         try:
#             connection = self.get_connection()
#             cursor = connection.cursor()

#             order_id = str(uuid.uuid4())
#             product_name = data.get('product_name')
#             number_shipped = data.get('number_shipped')
#             order_date = data.get('order_date')

#             if not order_id or not product_name or not number_shipped or not order_date:
#                 return jsonify({"error": "Missing required fields"}), 400
            
#             cursor.execute("SELECT QUANTITY_AVAILABLE FROM PRODUCT WHERE PRODUCT_NAME = %s", (product_name,))
#             product = cursor.fetchone()
#             if not product:
#                 return jsonify({"error": f"Product {product_name} not found"}), 404
            
#             current_quantity = product[0]

#             if current_quantity < number_shipped:
#                 return jsonify({'error': f'Not enough quantity for product {product_name}'}), 404

#             new_quantity = current_quantity - number_shipped

#             cursor.execute(""" UPDATE PRODUCT SET QUANTITY_AVAILABLE = %s WHERE PRODUCT_NAME = %s """, (new_quantity, product_name))

#             cursor.execute(""" INSERT INTO ORDERS (ORDERID, PRODUCTNAME, NUMBERSHIPPED, ORDERDATE) 
#                             VALUES (%s, %s, %s, %s)""", (order_id, product_name, number_shipped, order_date))
            
#             connection.commit()
#             return jsonify({'Message': 'Order placed product quantity added successfully'})
#         except snowflake.connector.Error as e:
#             return jsonify({"error": str(e)}), 500
#         finally:
#             cursor.close()
#             connection.close()
















