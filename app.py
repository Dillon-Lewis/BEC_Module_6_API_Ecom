from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, fields
from sqlalchemy import select, delete
from datetime import date
from typing import List

app = Flask(__name__)

###############CONNECTING DATABASE###############################

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Ziggyjone$3@localhost/Module_Ecom_API'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class= Base)   ## creating instance to say we are using python to fill our database
ma = Marshmallow(app)  ## Create instance of marshmallow to validate later

class Customers(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key= True)
    customer_name: Mapped[str] = mapped_column(db.String(75), nullable= False)
    username: Mapped[str] = mapped_column(db.String(75), nullable= False)
    email: Mapped[str] = mapped_column(db.String(75), nullable= False)
    phone: Mapped[str] = mapped_column(db.String(15))

    orders: Mapped[List['Orders']] = db.relationship(back_populates = 'customers')

order_products = db.Table(
    "order_products",
    Base.metadata,
    db.Column('orders_id', db.ForeignKey('orders.id'), primary_key = True),
    db.Column('products_id', db.ForeignKey('products.id'), primary_key = True)
)

class Orders(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key= True)
    date_ordered: Mapped[date] = mapped_column(db.Date, nullable= False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'))

    customer: Mapped['Customers'] = db.relationship(back_populates= 'orders')

    products: Mapped[List['Products']] = db.relationship(secondary = order_products)


class Products(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key= True)
    product_name: Mapped[str] = mapped_column(db.String(100), nullable= False)
    price: Mapped[float] = mapped_column(db.Float, nullable= False)
    Made_in: Mapped[str] = mapped_column(db.String(75))

#################VALIDATION WITH SCHEMA ########################

class CustomerSchema(ma.Schema):
    id = fields.Integer(required= False)
    customer_name = fields.String(required= True)
    username = fields.String(required= True)
    email = fields.String(required= True)
    phone = fields.String()
    class Meta:
        fields = ('id', 'customer_name', 'username', 'email', 'phone')

class OrderSchema(ma.Schema):
    id = fields.Integer(required= False)
    date_ordered = fields.Date(required= False)
    customer_id = fields.Integer(required= True)
    class Meta:
        fields = ('id', 'date_ordered', 'customer_id', 'items')

class ProductSchema(ma.Schema):
    id = fields.Integer(required= False)
    product_name = fields.String(required= True)
    price = fields.Float(required= True)
    Made_in = fields.String()
    class Meta:
        fields = ('id', 'product_name', 'price', 'Made_in')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many = True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many= True)

product_schema = ProductSchema()
products_schema = ProductSchema(many= True)

###########MAKING ROUTES#################################

######CUSTOMER######

@app.route('/')
def home():
    return "Welcome to the Ecom Database, the final push into backend core!"

@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify({e.messages}),400
    new_customer = Customers(customer_name= customer_data  ['customer_name'], username = customer_data['username'], email = customer_data['email'], phone = customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"Message": "New customer has been added!"}), 201


@app.route('/customers/<int:id>', methods = ['GET'])
def get_customer(id):
    query = select(Customers).where(Customers.id == id)
    result = db.session.execute(query).scalars().first()
    if result is None:
        return jsonify({'Error' : 'Customer not found!'}), 404


@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):

    query = select(Customers).where(Customers.id == id)
    result = db.session.execute(query).scalar()
    if result is None:
        return jsonify({"Error": "Customer not found"}), 404 
    customer = result
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    for field, value in customer_data.items():
        setattr(customer, field, value)
    db.session.commit()
    return jsonify({"Message": "Customer details have been updated!"})


@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    query = delete(Customers).where(Customers.id == id)
    result = db.session.execute(query)
    if result.rowcount == 0:
        return jsonify({"Error": "Customer not found"}) 
    db.session.commit()
    return jsonify({"Message": "Customer successfully deleted"})


# ########PRODUCTS

@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    new_product = Products(product_name= product_data['product_name'], price= product_data['price'], Made_in = product_data['Made_in'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"Message": "New product successfully added!"}), 201

@app.route('/products/<int:id>', methods = ['GET'])
def get_product(id):
    query = select(Products).where(Products.id == id)
    result = db.session.execute(query).scalars().first()
    if result is None:
        return jsonify({'Error' : 'Product was not found, please try again!'}), 404


@app.route('/products/<int:id>', methods=['PUT'])
def update_product_info(id):
    query = select(Products).where(Products.id == id)
    result = db.session.execute(query).scalar()
    if result is None:
        return jsonify({"Error": "Product can't be found, try again"}), 404
    product = result
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    for field, value in product_data.items():
        setattr(product, field, value)
    db.session.commit()
    return jsonify({"Message": "Product details have been updated!"})


@app.route('/products/<int:id>', methods=['DELETE'])
def remove_product(id):
    query = delete(Products).where(Products.id == id) 
    result = db.session.execute(query)
    if result.rowcount == 0:
        return jsonify({"Error": "Product not in the database, please try again."})
    db.session.commit()
    return jsonify({"Message": "Product successfully removed"})


@app.route("/products", methods= ['GET'])
def get_product_list():
    query = select(Products)
    result = db.session.execute(query).scalars() 
    product_list = result.all() 


# ############ORDERS

@app.route('/orders', methods=['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400 
    new_order = Orders(date_ordered= date.today(), customer_id= order_data['customer_id'])
    for item_id in order_data['items']:
        query = select(Orders).where(Orders.id == item_id)
        item = db.session.execute(query).scalar()
        new_order.products.append(item)
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"Message": "Order has been placed."}), 201


@app.route("/retrieve_order/<int:id>", methods=['GET'])
def retrieve_order(id):
    query = select(Orders).filter(Orders.id == id)
    order = db.session.execute(query).scalar()
    return products_schema.jsonify(order.products)













if __name__ == "__main__":
    app.run(debug= True)
