import os
from dotenv import load_dotenv
import psycopg2
from contextlib import contextmanager
from models import WebhookPayload

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_connection():
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def insert_data(payload: WebhookPayload):
    with get_connection() as conn:
        cur = conn.cursor()

        restaurant = payload.properties.Restaurant
        customer = payload.properties.Customer
        order = payload.properties.Order
        tax_list = payload.properties.Tax or []
        discount_list = payload.properties.Discount or []
        items = payload.properties.OrderItem or []
        part_payments = order.part_payments or []

        # Insert Restaurant
        cur.execute("""
            INSERT INTO restaurants (rest_id, res_name, address, contact_information)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (rest_id) DO NOTHING
        """, (
            restaurant.restID,
            restaurant.res_name,
            restaurant.address,
            restaurant.contact_information
        ))

        # Insert Customer
        cur.execute("""
            INSERT INTO customers (name, address, phone, gstin)
            VALUES (%s, %s, %s, %s)
            RETURNING customer_id
        """, (
            customer.name,
            customer.address,
            customer.phone,
            customer.gstin
        ))
        customer_id = cur.fetchone()[0]

        # Insert Order
        cur.execute("""
            INSERT INTO orders (
                order_id, customer_id, rest_id, customer_invoice_id, delivery_charges,
                order_type, payment_type, table_no, no_of_persons, discount_total,
                tax_total, round_off, core_total, total, created_on, order_from,
                order_from_id, sub_order_type, packaging_charge, status, comment,
                biller, assignee
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            order.orderID,
            customer_id,
            restaurant.restID,
            order.customer_invoice_id,
            order.delivery_charges,
            order.order_type,
            order.payment_type,
            order.table_no,
            order.no_of_persons,
            order.discount_total,
            order.tax_total,
            order.round_off,
            order.core_total,
            order.total,
            order.created_on,
            order.order_from,
            order.order_from_id,
            order.sub_order_type,
            order.packaging_charge,
            order.status,
            order.comment,
            order.biller,
            order.assignee
        ))

        # Insert Taxes
        for tax in tax_list:
            cur.execute("""
                INSERT INTO taxes (order_id, title, rate, amount)
                VALUES (%s, %s, %s, %s)
            """, (
                order.orderID,
                tax.title,
                tax.rate,
                tax.amount
            ))

        # Insert Discounts
        for discount in discount_list:
            cur.execute("""
                INSERT INTO discounts (order_id, title, type, rate, amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order.orderID,
                discount.title,
                discount.type,
                discount.rate,
                discount.amount
            ))

        # Insert Order Items and Addons
        for item in items:
            cur.execute("""
                INSERT INTO order_items (
                    itemid, order_id, name, itemcode, vendoritemcode,
                    specialnotes, price, quantity, total, category_name,
                    sap_code, discount, tax
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT DO NOTHING
            """, (
                item.itemid,
                order.orderID,
                item.name,
                item.itemcode,
                item.vendoritemcode,
                item.specialnotes,
                item.price,
                item.quantity,
                item.total,
                item.category_name,
                item.sap_code,
                item.discount,
                item.tax
            ))

            for addon in item.addon or []:
                cur.execute("""
                    INSERT INTO addons (
                        addon_id, itemid, group_name, name, price, quantity,
                        sap_code, addon_group_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    addon.addon_id,
                    item.itemid,
                    addon.group_name,
                    addon.name,
                    addon.price,
                    addon.quantity,
                    addon.sap_code,
                    addon.addon_group_id
                ))

        # Insert Part Payments
        for pp in part_payments:
            cur.execute("""
                INSERT INTO part_payments (
                    order_id, payment_type, amount, custome_payment_type
                ) VALUES (%s, %s, %s, %s)
            """, (
                order.orderID,
                pp.payment_type,
                pp.amount,
                pp.custome_payment_type
            ))

        conn.commit()
        cur.close()
        print("[DB] ✅ All records inserted successfully.")