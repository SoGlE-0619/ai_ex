"""꺼내오는 자리 ― 데이터베이스에서 필요한 것을 조립해서 돌려준다.

DB 없이는 한 줄도 못 돈다. 여럿을 엮어야 일이 되는 파일이라 features/ 에 둔다.
"""

# 🔴 오늘 바뀐 줄 ― 어제까지는  from app.db import dicts, one  였다
from app.core.db import dicts, one


def customer_list(limit=None):
    """고객 목록 + 각자 구매 건수."""
    rows = dicts("""
        SELECT customers.customer_id, customers.name, customers.age, customers.gender,
               customers.skin_type, customers.city,
               COUNT(purchases.purchase_id) AS n_purchases
        FROM customers
        LEFT JOIN purchases ON purchases.customer_id = customers.customer_id
                           AND purchases.is_holdout = 0
        GROUP BY customers.customer_id
        ORDER BY customers.customer_id
    """)
    return rows[:limit] if limit else rows


def dashboard(customer_id):
    """한 고객에 대해 아는 것을 전부 모아서 돌려준다. 없는 고객이면 None."""
    profile = dicts("""
        SELECT customer_id, name, age, gender, skin_type, city
        FROM customers WHERE customer_id = ?
    """, (customer_id,))

    if not profile:
        return None

    purchases = dicts("""
        SELECT products.product_id, products.name, products.category, products.price,
               purchases.purchased_at, purchases.rating, purchases.review
        FROM purchases
        JOIN products ON purchases.product_id = products.product_id
        WHERE purchases.customer_id = ? AND purchases.is_holdout = 0
        ORDER BY purchases.purchased_at DESC
    """, (customer_id,))

    by_category = {}
    for row in purchases:
        by_category[row["category"]] = by_category.get(row["category"], 0) + 1

    ratings = [row["rating"] for row in purchases if row["rating"] is not None]

    return {
        "customer": {**profile[0], "n_purchases": len(purchases)},
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "total_spent": sum(row["price"] for row in purchases),
        "by_category": by_category,
        "purchases": purchases,
    }


if __name__ == "__main__":
    rows = customer_list()
    print(f"고객 {len(rows)}명")

    board = dashboard(rows[0]["customer_id"])
    customer = board["customer"]
    print(f"  {customer['name']} · {customer['skin_type']} · 구매 {customer['n_purchases']}건"
          f" · 누적 {board['total_spent']:,}원")
