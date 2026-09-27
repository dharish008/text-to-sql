"""
Verified Golden Question-SQL exemplars for dynamic few-shot retrieval.
"""

GOLDEN_PAIRS = [
    {
        "question": "What was the total rental payment revenue collected in July 2005?",
        "sql": """SELECT SUM(amount) AS total_revenue
FROM payment
WHERE payment_date >= '2005-07-01' AND payment_date < '2005-08-01';"""
    },
    {
        "question": "Who are the top 5 customers by total spending?",
        "sql": """SELECT c.customer_id, c.first_name, c.last_name, SUM(p.amount) AS total_spent
FROM customer c
JOIN payment p ON c.customer_id = p.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC
LIMIT 5;"""
    },
    {
        "question": "Which film categories generated the most revenue?",
        "sql": """SELECT c.name AS category, SUM(p.amount) AS total_revenue
FROM category c
JOIN film_category fc ON c.category_id = fc.category_id
JOIN film f ON fc.film_id = f.film_id
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
JOIN payment p ON r.rental_id = p.rental_id
GROUP BY c.name
ORDER BY total_revenue DESC;"""
    },
    {
        "question": "How many rentals are currently checked out and not yet returned?",
        "sql": """SELECT COUNT(*) AS active_rentals
FROM rental
WHERE return_date IS NULL;"""
    },
    {
        "question": "Find the top 3 most rented films in terms of total rental count.",
        "sql": """SELECT f.title, COUNT(r.rental_id) AS rental_count
FROM film f
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
GROUP BY f.film_id, f.title
ORDER BY rental_count DESC
LIMIT 3;"""
    },
    {
        "question": "List all active customers living in the city of London.",
        "sql": """SELECT c.customer_id, c.first_name, c.last_name, c.email
FROM customer c
JOIN address a ON c.address_id = a.address_id
JOIN city ci ON a.city_id = ci.city_id
WHERE ci.city ILIKE 'London' AND c.active = 1;"""
    }
]