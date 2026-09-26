"""
Comprehensive semantic metadata catalog for Pagila / Sakila.
Provides business context, metrics, join hints, and column glossaries
for LLM Text-to-SQL generation.
"""

COLUMN_ENUMS = {
    "film": {
        "rating": ["G", "PG", "PG-13", "R", "NC-17"],
        "special_features": ["Trailers", "Commentaries", "Deleted Scenes", "Behind the Scenes"]
    },
    "category": {
        "name": [
            "Action", "Animation", "Children", "Classics", "Comedy", "Documentary",
            "Drama", "Family", "Foreign", "Games", "Horror", "Music", "New",
            "Sci-Fi", "Sports", "Travel"
        ]
    },
    "customer": {
        "active": [1, 0],
        "activebool": [True, False]
    },
    "staff": {
        "active": [True, False]
    },
    "language": {
        "name": ["English", "Italian", "Japanese", "Mandarin", "French", "German"]
    }
}

SEMANTIC_CATALOG = {
    # ---------------------------------------------------------
    # Core Transaction & Fact Entities
    # ---------------------------------------------------------
    "payment": {
        "description": "Records monetary transactions and customer payments for film rentals.",
        "business_rules": [
            "Gross rental revenue is calculated using SUM(amount).",
            "Transactions are denominated in USD ($).",
            "Group or filter by payment_date for monthly/yearly temporal revenue analysis.",
            "Links to rental via rental_id and customer via customer_id."
        ],
        "column_glossary": {
            "payment_id": "Primary key for the payment record.",
            "customer_id": "Foreign key to customer who made the payment.",
            "staff_id": "Foreign key to staff member who processed the transaction.",
            "rental_id": "Foreign key to rental transaction associated with this charge.",
            "amount": "Monetary total charged for the rental in USD.",
            "payment_date": "Timestamp when the payment occurred."
        }
    },
    "rental": {
        "description": "Tracks rental lifecycle events when inventory discs are checked out and returned.",
        "business_rules": [
            "An ongoing / unreturned rental is indicated by return_date IS NULL.",
            "Total rental volume count is COUNT(rental_id).",
            "Rental duration in days: EXTRACT(EPOCH FROM (return_date - rental_date)) / 86400.",
            "Connects to film via inventory (rental -> inventory -> film)."
        ],
        "column_glossary": {
            "rental_id": "Primary key for the rental event.",
            "rental_date": "Timestamp when the disc was checked out.",
            "inventory_id": "Foreign key to inventory table indicating the physical disc copy.",
            "customer_id": "Foreign key to customer renting the item.",
            "return_date": "Timestamp when the disc was returned. NULL means still checked out.",
            "staff_id": "Foreign key to staff member checking out the disc.",
            "last_update": "Timestamp of the last row update."
        }
    },
    "inventory": {
        "description": "Represents individual physical DVD copies stocked at specific retail store locations.",
        "business_rules": [
            "Acts as the essential junction bridge connecting rentals to film catalog items.",
            "Count of available physical inventory copies is COUNT(inventory_id)."
        ],
        "column_glossary": {
            "inventory_id": "Primary key identifying an individual physical disc copy.",
            "film_id": "Foreign key pointing to the film catalog.",
            "store_id": "Foreign key indicating which retail store stocks this disc.",
            "last_update": "Timestamp of the last row update."
        }
    },

    # ---------------------------------------------------------
    # Catalog & Media Dimensions
    # ---------------------------------------------------------
    "film": {
        "description": "Master catalog of movies available for rent across all stores.",
        "business_rules": [
            "length represents movie runtime in minutes.",
            "rental_rate is the baseline checkout cost per rental in USD.",
            "replacement_cost is charged if a copy is lost or damaged.",
            "rating options: 'G', 'PG', 'PG-13', 'R', 'NC-17'."
        ],
        "column_glossary": {
            "film_id": "Primary key for the film.",
            "title": "Movie title.",
            "description": "Brief plot summary.",
            "release_year": "Year the movie was released.",
            "language_id": "Foreign key pointing to language table for audio language.",
            "original_language_id": "Foreign key pointing to original audio language if dubbed.",
            "rental_duration": "Default loan period allowance in days.",
            "rental_rate": "Cost to rent the film for the rental duration in USD.",
            "length": "Movie duration in minutes.",
            "replacement_cost": "Penalty fee if the disc is lost or destroyed.",
            "rating": "MPAA rating ('G', 'PG', 'PG-13', 'R', 'NC-17').",
            "last_update": "Timestamp of the last row update.",
            "special_features": "Array/text of DVD extras (e.g. Trailers, Commentaries, Deleted Scenes).",
            "fulltext": "PostgreSQL tsvector column for full-text search indexing."
        }
    },
    "category": {
        "description": "Genre categories assigned to movies.",
        "business_rules": [
            "Connects to film via the film_category junction table."
        ],
        "column_glossary": {
            "category_id": "Primary key for the film genre.",
            "name": "Name of the genre (e.g., Action, Animation, Comedy, Sci-Fi).",
            "last_update": "Timestamp of the last row update."
        }
    },
    "film_category": {
        "description": "Junction table mapping films to their respective genre categories (Many-to-Many).",
        "business_rules": [
            "Join path: film JOIN film_category ON film.film_id = film_category.film_id JOIN category ON film_category.category_id = category.category_id."
        ],
        "column_glossary": {
            "film_id": "Foreign key to film.",
            "category_id": "Foreign key to category.",
            "last_update": "Timestamp of the last row update."
        }
    },
    "actor": {
        "description": "Master list of actors who perform in films.",
        "business_rules": [
            "Connects to film via the film_actor junction table.",
            "Full actor name can be assembled via: first_name || ' ' || last_name."
        ],
        "column_glossary": {
            "actor_id": "Primary key for the actor.",
            "first_name": "Actor's given name.",
            "last_name": "Actor's surname.",
            "last_update": "Timestamp of the last row update."
        }
    },
    "film_actor": {
        "description": "Junction table linking actors to movies they appeared in (Many-to-Many).",
        "business_rules": [
            "Join path: actor JOIN film_actor ON actor.actor_id = film_actor.actor_id JOIN film ON film_actor.film_id = film.film_id."
        ],
        "column_glossary": {
            "actor_id": "Foreign key to actor.",
            "film_id": "Foreign key to film.",
            "last_update": "Timestamp of the last row update."
        }
    },
    "language": {
        "description": "Spoken languages for film audio tracks.",
        "business_rules": [
            "Links to film.language_id and film.original_language_id."
        ],
        "column_glossary": {
            "language_id": "Primary key for the language.",
            "name": "Language name (e.g. English, Italian, Japanese, Mandarin).",
            "last_update": "Timestamp of the last row update."
        }
    },

    # ---------------------------------------------------------
    # Customers, Staff, and Store Entities
    # ---------------------------------------------------------
    "customer": {
        "description": "Customer profiles, account status, and store registration.",
        "business_rules": [
            "An active account has active = 1 (or activebool = TRUE).",
            "Filter active = 1 for active user metrics unless inactive users are requested.",
            "Full customer name: first_name || ' ' || last_name."
        ],
        "column_glossary": {
            "customer_id": "Primary key for the customer.",
            "store_id": "Foreign key to store where the customer originally signed up.",
            "first_name": "Customer given name.",
            "last_name": "Customer surname.",
            "email": "Customer email address.",
            "address_id": "Foreign key to address.",
            "activebool": "Boolean flag for account activity status.",
            "create_date": "Date customer account was created.",
            "last_update": "Timestamp of the last row update.",
            "active": "Integer status flag (1 = active, 0 = inactive)."
        }
    },
    "staff": {
        "description": "Store employees and management staff who process rentals and manage stores.",
        "business_rules": [
            "active = TRUE denotes an employed staff member."
        ],
        "column_glossary": {
            "staff_id": "Primary key for the staff member.",
            "first_name": "Staff member given name.",
            "last_name": "Staff member surname.",
            "address_id": "Foreign key to address.",
            "email": "Staff corporate email.",
            "store_id": "Foreign key indicating assigned store branch.",
            "active": "Boolean status indicating active employment.",
            "username": "System login username.",
            "password": "Password hash.",
            "last_update": "Timestamp of the last row update.",
            "picture": "Binary blob of employee photograph."
        }
    },
    "store": {
        "description": "Retail store branch locations.",
        "business_rules": [
            "Links to staff for store manager (manager_staff_id).",
            "Links to address for geographic location."
        ],
        "column_glossary": {
            "store_id": "Primary key for the store branch.",
            "manager_staff_id": "Foreign key to staff member managing this branch.",
            "address_id": "Foreign key to address for physical store location.",
            "last_update": "Timestamp of the last row update."
        }
    },

    # ---------------------------------------------------------
    # Geographic & Contact Dimensions
    # ---------------------------------------------------------
    "address": {
        "description": "Physical postal street addresses for stores, staff, and customers.",
        "business_rules": [
            "district often denotes state or province.",
            "Links upward to city via city_id."
        ],
        "column_glossary": {
            "address_id": "Primary key for the address.",
            "address": "Primary street address.",
            "address2": "Secondary street or unit number.",
            "district": "Region, province, or state.",
            "city_id": "Foreign key to city.",
            "postal_code": "Postal / ZIP code.",
            "phone": "Telephone contact number.",
            "last_update": "Timestamp of the last row update."
        }
    },
    "city": {
        "description": "City names linked to countries.",
        "business_rules": [
            "Join path to country: city JOIN country ON city.country_id = country.country_id."
        ],
        "column_glossary": {
            "city_id": "Primary key for the city.",
            "city": "Name of the municipality or city.",
            "country_id": "Foreign key to country.",
            "last_update": "Timestamp of the last row update."
        }
    },
    "country": {
        "description": "Country dimension for geographic reporting.",
        "business_rules": [
            "Used to aggregate sales, customer counts, or rental distributions by country."
        ],
        "column_glossary": {
            "country_id": "Primary key for the country.",
            "country": "Nation / country name.",
            "last_update": "Timestamp of the last row update."
        }
    },

    # ---------------------------------------------------------
    # Reporting Views (Pre-Joined Analytical Objects)
    # ---------------------------------------------------------
    "sales_by_film_category": {
        "description": "Reporting view displaying total gross rental sales aggregated by film genre.",
        "business_rules": [
            "Use when users ask for revenue or sales per category without needing complex raw joins."
        ],
        "column_glossary": {
            "category": "Film genre name.",
            "total_sales": "Total gross rental revenue collected in USD."
        }
    },
    "sales_by_store": {
        "description": "Reporting view summarizing gross rental revenue and manager names per retail store.",
        "business_rules": [
            "Use when comparing sales performance between stores."
        ],
        "column_glossary": {
            "store": "Store identifier / location identifier.",
            "manager": "Store manager's full name.",
            "total_sales": "Total gross rental revenue generated by this store."
        }
    },
    "actor_info": {
        "description": "Reporting view providing actor full names alongside a summary of their films by category.",
        "business_rules": [
            "Pre-aggregates film titles grouped by category for each actor."
        ],
        "column_glossary": {
            "actor_id": "Identifier of the actor.",
            "first_name": "Actor given name.",
            "last_name": "Actor surname.",
            "film_info": "Formatted string summarizing films grouped by category."
        }
    },
    "film_list": {
        "description": "Convenience reporting view listing movies with their categories, prices, runtimes, and comma-separated cast.",
        "business_rules": [
            "Use when user wants movie details, prices, and actor names in a single query."
        ],
        "column_glossary": {
            "fid": "Film ID.",
            "title": "Film title.",
            "description": "Plot summary.",
            "category": "Genre category name.",
            "price": "Rental rate.",
            "length": "Runtime in minutes.",
            "rating": "MPAA rating.",
            "actors": "Comma-separated list of actors."
        }
    },
    "nicer_but_slower_film_list": {
        "description": "Alternative film reporting view with title-cased actor names.",
        "business_rules": [
            "Prefer 'film_list' for standard querying unless title-cased actor formatting is explicitly requested."
        ],
        "column_glossary": {
            "fid": "Film ID.",
            "title": "Film title.",
            "description": "Plot summary.",
            "category": "Genre category name.",
            "price": "Rental rate.",
            "length": "Runtime in minutes.",
            "rating": "MPAA rating.",
            "actors": "Comma-separated list of title-cased actors."
        }
    },
    "customer_list": {
        "description": "Flattened reporting view combining customer profiles with full address, city, and country details.",
        "business_rules": [
            "Use when querying customer addresses or geographic distribution to avoid joining 4 separate tables."
        ],
        "column_glossary": {
            "id": "Customer ID.",
            "name": "Customer full name.",
            "address": "Street address.",
            "zip code": "Postal code.",
            "phone": "Telephone contact.",
            "city": "City name.",
            "country": "Country name.",
            "notes": "Account status notes (e.g. active).",
            "sid": "Store ID."
        }
    },
    "staff_list": {
        "description": "Flattened reporting view combining staff profiles with their address and location info.",
        "business_rules": [
            "Avoids multi-table joins when querying staff geographic locations."
        ],
        "column_glossary": {
            "id": "Staff member ID.",
            "name": "Staff member full name.",
            "address": "Street address.",
            "zip code": "Postal code.",
            "phone": "Telephone contact.",
            "city": "City name.",
            "country": "Country name.",
            "sid": "Assigned store ID."
        }
    }
}

JOIN_PATHS = {
    "film": [
        "To Category: film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id",
        "To Actor: film f JOIN film_actor fa ON f.film_id = fa.film_id JOIN actor a ON fa.actor_id = a.actor_id",
        "To Inventory: film f JOIN inventory i ON f.film_id = i.film_id",
        "To Rental: film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id",
        "To Revenue/Payment: film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id JOIN payment p ON r.rental_id = p.rental_id"
    ],
    "rental": [
        "To Customer: rental r JOIN customer c ON r.customer_id = c.customer_id",
        "To Film: rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN film f ON i.film_id = f.film_id",
        "To Category: rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN film_category fc ON i.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id",
        "To Payment: rental r JOIN payment p ON r.rental_id = p.rental_id",
        "To Store: rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN store s ON i.store_id = s.store_id"
    ],
    "payment": [
        "To Customer: payment p JOIN customer c ON p.customer_id = c.customer_id",
        "To Rental: payment p JOIN rental r ON p.rental_id = r.rental_id",
        "To Film: payment p JOIN rental r ON p.rental_id = r.rental_id JOIN inventory i ON r.inventory_id = i.inventory_id JOIN film f ON i.film_id = f.film_id",
        "To Staff: payment p JOIN staff s ON p.staff_id = s.staff_id"
    ],
    "customer": [
        "To Address/Location: customer c JOIN address a ON c.address_id = a.address_id JOIN city ci ON a.city_id = ci.city_id JOIN country co ON ci.country_id = co.country_id",
        "To Rentals: customer c JOIN rental r ON c.customer_id = r.customer_id",
        "To Payments: customer c JOIN payment p ON c.customer_id = p.customer_id"
    ],
    "actor": [
        "To Film: actor a JOIN film_actor fa ON a.actor_id = fa.actor_id JOIN film f ON fa.film_id = f.film_id",
        "To Category: actor a JOIN film_actor fa ON a.actor_id = fa.actor_id JOIN film_category fc ON fa.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id"
    ],
    "store": [
        "To Manager: store s JOIN staff m ON s.manager_staff_id = m.staff_id",
        "To Location: store s JOIN address a ON s.address_id = a.address_id JOIN city ci ON a.city_id = ci.city_id JOIN country co ON ci.country_id = co.country_id",
        "To Inventory: store s JOIN inventory i ON s.store_id = i.store_id"
    ]
}