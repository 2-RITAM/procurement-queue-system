import mysql.connector
from mysql.connector import Error
from datetime import datetime, date, timedelta

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="2ritamjha@",       # CHANGE THIS
        database="procurement_system"
    )

# Small helper used to close DB resources
def close_connection(conn, cursor):
    if cursor:
        cursor.close()

    if conn:
        conn.close()

# Create a procurement ID
def generate_procurement_id():
    now = datetime.now()

    prefix = "KP"
    date_part = now.strftime("%y%m%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE procurement_id LIKE %s
    """, (prefix + date_part + "%",))

    count = cursor.fetchone()[0] + 1

    close_connection(conn, cursor)

    return f"{prefix}{date_part}{count:02d}"

# Farmer registration
def register_farmer():

    print("\n" + "=" * 50)
    print("              REGISTER FARMER")
    print("=" * 50)

    while True:

        name = input("Enter farmer name: ").strip()

        if name and all(char.isalpha() or char == " " for char in name):
            break

        print("Invalid name. Please use alphabets and spaces only.")

    while True:

        mobile = input("Enter mobile number: ").strip()

        if mobile.isdigit() and len(mobile) == 10:
            break

        print("Invalid mobile number. Enter exactly 10 digits.")

    while True:

        registration_id = input(
            "Enter farmer registration ID: "
        ).strip()

        if registration_id:
            break

        print("Registration ID cannot be empty.")

    while True:

        village = input("Enter village/location: ").strip()

        if village:
            break

        print("Village/location cannot be empty.")

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO farmers
        (name, mobile, registration_id, village)
        VALUES (%s, %s, %s, %s)
        """

        values = (
            name,
            mobile,
            registration_id,
            village
        )

        cursor.execute(query, values)

        conn.commit()

        print("\nFarmer registered successfully!")
        print("Farmer ID:", cursor.lastrowid)

    except Error as e:

        print("\nError registering farmer.")

        if "Duplicate entry" in str(e):
            print("This registration ID already exists.")

        else:
            print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Show active procurement centers
def view_centers():

    print("\n" + "=" * 70)
    print("                 PROCUREMENT CENTERS")
    print("=" * 70)

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                center_id,
                center_name,
                location,
                daily_capacity,
                slot_capacity,
                slot_duration,
                status
            FROM procurement_centers
            WHERE status = 'Active'
            ORDER BY center_id
        """)

        centers = cursor.fetchall()

        if not centers:
            print("No active procurement centers found.")
            return

        print(
            "\nID | Center | Location | Daily Capacity | "
            "Farmers/Slot | Duration"
        )

        print("-" * 70)

        for center in centers:

            print(
                center[0], "|",
                center[1], "|",
                center[2], "|",
                center[3], "kg |",
                center[4], "|",
                center[5], "min"
            )

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Create the day's slots if needed
def generate_slots_for_date(center_id, selected_date):

    """
    Creates slots automatically if they do not already exist.

    Prototype operating hours:
    09:00 AM to 05:00 PM

    Slot duration comes from procurement_centers.
    """

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT slot_capacity, slot_duration
            FROM procurement_centers
            WHERE center_id = %s
            AND status = 'Active'
        """, (center_id,))

        center = cursor.fetchone()

        if center is None:
            print("Procurement center not found.")
            return False

        slot_capacity = center[0]
        slot_duration = center[1]

        cursor.execute("""
            SELECT COUNT(*)
            FROM slots
            WHERE center_id = %s
            AND slot_date = %s
        """, (center_id, selected_date))

        existing_slots = cursor.fetchone()[0]

        if existing_slots > 0:
            return True

        current_time = datetime.strptime(
            "09:00", "%H:%M"
        )

        closing_time = datetime.strptime(
            "17:00", "%H:%M"
        )

        while current_time < closing_time:

            end_time = current_time + timedelta(
                minutes=slot_duration
            )

            if end_time > closing_time:
                break

            cursor.execute("""
                INSERT INTO slots
                (
                    center_id,
                    slot_date,
                    start_time,
                    end_time,
                    maximum_farmers,
                    booked_farmer,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, 0, 'Available')
            """, (
                center_id,
                selected_date,
                current_time.strftime("%H:%M:%S"),
                end_time.strftime("%H:%M:%S"),
                slot_capacity
            ))

            current_time = end_time

        conn.commit()

        return True

    except Error as e:

        print("Error generating slots:", e)
        return False

    finally:

        close_connection(conn, cursor)

# Show slots for a center and date
def view_available_slots(center_id, selected_date):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            slot_id,
            start_time,
            end_time,
            maximum_farmers,
            booked_farmer,
            status
        FROM slots
        WHERE center_id = %s
        AND slot_date = %s
        ORDER BY start_time
        """

        cursor.execute(
            query,
            (center_id, selected_date)
        )

        slots = cursor.fetchall()

        if not slots:
            print("No slots available for this date.")
            return []

        print("\n" + "=" * 70)
        print("                  AVAILABLE SLOTS")
        print("=" * 70)

        print(
            "\nID | Time | Capacity | Booked | Remaining | Status"
        )

        print("-" * 70)

        available_slots = []

        for slot in slots:

            remaining = slot[3] - slot[4]

            status = slot[5]

            if remaining <= 0:
                status = "FUL"

            if status == "Available":

                available_slots.append(slot)

            display_status = "Full" if status == "FUL" else status

            print(
                slot[0], "|",
                str(slot[1])[:5],
                "-",
                str(slot[2])[:5],
                "|",
                slot[3], "|",
                slot[4], "|",
                remaining, "|",
                display_status
            )

        return available_slots

    except Error as e:

        print("Database error:", e)
        return []

    finally:

        close_connection(conn, cursor)

# Book a slot
def book_procurement_slot():

    print("\n" + "=" * 60)
    print("              BOOK PROCUREMENT SLOT")
    print("=" * 60)

    try:

        farmer_id = int(
            input("Enter Farmer ID: ")
        )

    except ValueError:

        print("Invalid Farmer ID.")
        return

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, mobile, registration_id
            FROM farmers
            WHERE farmer_id = %s
        """, (farmer_id,))

        farmer = cursor.fetchone()

        if farmer is None:

            print("Farmer not found.")
            return

        print("\nFarmer:", farmer[0])
        print("Mobile:", farmer[1])
        print("Registration ID:", farmer[2])

    except Error as e:

        print("Database error:", e)
        close_connection(conn, cursor)
        return

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    view_centers()

    try:

        center_id = int(
            input("\nEnter Procurement Center ID: ")
        )

    except ValueError:

        print("Invalid center ID.")
        return

    while True:

        try:

            quantity = float(
                input(
                    "Enter expected onion quantity (kg): "
                )
            )

            if quantity <= 0:

                print("Quantity must be greater than 0.")
                continue

            break

        except ValueError:

            print("Please enter a valid quantity.")

    while True:

        date_input = input(
            "Enter preferred date (YYYY-MM-DD): "
        ).strip()

        try:

            selected_date = datetime.strptime(
                date_input,
                "%Y-%m-%d"
            ).date()

            if selected_date < date.today():

                print("Date cannot be in the past.")
                continue

            break

        except ValueError:

            print(
                "Invalid date. Use YYYY-MM-DD."
            )

    if not generate_slots_for_date(
        center_id,
        selected_date
    ):

        return

    available_slots = view_available_slots(
        center_id,
        selected_date
    )

    if not available_slots:

        print("\nNo available slots.")
        return

    try:

        slot_id = int(
            input("\nEnter Slot ID: ")
        )

    except ValueError:

        print("Invalid slot ID.")
        return

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                maximum_farmers,
                booked_farmer,
                status
            FROM slots
            WHERE slot_id = %s
            AND center_id = %s
            AND slot_date = %s
        """, (
            slot_id,
            center_id,
            selected_date
        ))

        slot = cursor.fetchone()

        if slot is None:

            print("Invalid slot.")
            return

        maximum_farmers = slot[0]
        booked_farmer = slot[1]
        status = slot[2]

        if status != "Available" or \
                booked_farmer >= maximum_farmers:

            print("\nThis slot is full or unavailable.")
            return

        procurement_id = generate_procurement_id()

        cursor.execute("""
            SELECT COALESCE(MAX(token_number), 0) + 1
            FROM bookings
            WHERE center_id = %s
            AND booking_date = %s
        """, (
            center_id,
            selected_date
        ))

        token_number = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO bookings
            (
                procurement_id,
                farmer_id,
                center_id,
                slot_id,
                expected_quantity,
                token_number,
                booking_date,
                status
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, 'Slot Booked')
        """, (
            procurement_id,
            farmer_id,
            center_id,
            slot_id,
            quantity,
            token_number,
            selected_date
        ))

        booking_id = cursor.lastrowid

        new_booked_count = booked_farmer + 1

        new_status = "FUL"

        if new_booked_count < maximum_farmers:
            new_status = "Available"

        cursor.execute("""
            UPDATE slots
            SET booked_farmer = %s,
                status = %s
            WHERE slot_id = %s
        """, (
            new_booked_count,
            new_status,
            slot_id
        ))

        cursor.execute("""
            INSERT INTO procurement
            (
                procurement_id,
                booking_id,
                payment_status
            )
            VALUES
            (%s, %s, 'Pending')
        """, (
            procurement_id,
            booking_id
        ))

        message = (
            f"Booking confirmed. "
            f"Procurement ID: {procurement_id}. "
            f"Token: {token_number}. "
            f"Date: {selected_date}. "
            f"Please arrive at your scheduled slot."
        )

        cursor.execute("""
            INSERT INTO notifications
            (
                farmer_id,
                procurement_id,
                message,
                notification_type,
                status
            )
            VALUES
            (%s, %s, %s, 'Booking Confirmed', 'Sent')
        """, (
            farmer_id,
            procurement_id,
            message
        ))

        conn.commit()

        print("\n" + "=" * 60)
        print("             BOOKING CONFIRMED")
        print("=" * 60)

        print("Procurement ID :", procurement_id)
        print("Farmer Name    :", farmer[0])
        print("Center ID      :", center_id)
        print("Expected Qty   :", quantity, "kg")
        print("Date           :", selected_date)
        print("Token Number   :", token_number)
        print("Status         : Slot Booked")

        print("\nSMS Notification:")
        print(message)

    except Error as e:

        if conn:
            conn.rollback()

        print("\nBooking failed.")
        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Today's live queue
def view_live_queue():

    print("\n" + "=" * 75)
    print("                    TODAY'S PROCUREMENT")
    print("=" * 75)

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = date.today()

        cursor.execute("""
            SELECT
                token_number,
                procurement_id,
                status
            FROM bookings
            WHERE booking_date = %s
            AND status IN
            (
                'Farmer Arrived',
                'Quality Inspection',
                'Quantity Verified',
                'Payment Processing'
            )
            ORDER BY token_number
            LIMIT 1
        """, (today,))

        current = cursor.fetchone()

        if current:

            currently_serving = current["token_number"]

        else:

            cursor.execute("""
                SELECT MIN(token_number) AS first_token
                FROM bookings
                WHERE booking_date = %s
                AND status = 'Slot Booked'
            """, (today,))

            result = cursor.fetchone()

            if result["first_token"] is None:

                currently_serving = 0

            else:

                currently_serving = result["first_token"]

        cursor.execute("""
            SELECT COUNT(*) AS processed
            FROM bookings
            WHERE booking_date = %s
            AND status = 'Payment Completed'
        """, (today,))

        processed = cursor.fetchone()["processed"]

        cursor.execute("""
            SELECT COUNT(*) AS waiting
            FROM bookings
            WHERE booking_date = %s
            AND status = 'Slot Booked'
        """, (today,))

        waiting = cursor.fetchone()["waiting"]

        cursor.execute("""
            SELECT
                AVG(
                    TIMESTAMPDIFF(
                        MINUTE,
                        arrival_time,
                        completion_time
                    )
                ) AS avg_processing
            FROM procurement
            WHERE completion_time IS NOT NULL
            AND arrival_time IS NOT NULL
        """)

        avg_result = cursor.fetchone()

        avg_processing = avg_result["avg_processing"]

        if avg_processing is None:

            avg_processing = 5.0

        print("\nCurrently serving :", currently_serving)
        print("Farmers processed  :", processed)
        print("Farmers waiting    :", waiting)

        print(
            "Average processing:",
            round(avg_processing, 2),
            "minutes"
        )

        print("\n" + "-" * 75)

        cursor.execute("""
            SELECT
                b.token_number,
                b.procurement_id,
                f.name,
                b.expected_quantity,
                b.status
            FROM bookings b
            JOIN farmers f
                ON b.farmer_id = f.farmer_id
            WHERE b.booking_date = %s
            AND b.status != 'Cancelled'
            AND b.status != 'Payment Completed'
            ORDER BY b.token_number
        """, (today,))

        queue = cursor.fetchall()

        if not queue:

            print("No active queue today.")
            return

        print(
            "\nToken | Farmer | Expected Qty | Status"
        )

        print("-" * 75)

        for item in queue:

            print(
                item["token_number"], "|",
                item["name"], "|",
                item["expected_quantity"], "kg |",
                item["status"]
            )

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Check a farmer's queue position
def track_queue():

    print("\n" + "=" * 60)
    print("                  TRACK YOUR QUEUE")
    print("=" * 60)

    procurement_id = input(
        "Enter Procurement ID: "
    ).strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                b.procurement_id,
                b.token_number,
                b.booking_date,
                b.status,
                b.expected_quantity,
                f.name AS farmer_name,
                pc.center_name
            FROM bookings b
            JOIN farmers f
                ON b.farmer_id = f.farmer_id
            JOIN procurement_centers pc
                ON b.center_id = pc.center_id
            WHERE b.procurement_id = %s
        """, (procurement_id,))

        booking = cursor.fetchone()

        if booking is None:

            print("Procurement ID not found.")
            return

        print("\nFarmer Name       :", booking["farmer_name"])
        print("Procurement ID    :", booking["procurement_id"])
        print("Procurement Center:", booking["center_name"])
        print("Token             :", booking["token_number"])
        print("Expected Quantity :", booking["expected_quantity"], "kg")
        print("Date              :", booking["booking_date"])
        print("Status            :", booking["status"])

        if booking["status"] == "Slot Booked":

            cursor.execute("""
                SELECT COUNT(*) AS ahead
                FROM bookings
                WHERE center_id = (
                    SELECT center_id
                    FROM bookings
                    WHERE procurement_id = %s
                )
                AND booking_date = %s
                AND token_number < %s
                AND status NOT IN
                (
                    'Payment Completed',
                    'Cancelled'
                )
            """, (
                procurement_id,
                booking["booking_date"],
                booking["token_number"]
            ))

            ahead = cursor.fetchone()["ahead"]

            cursor.execute("""
                SELECT
                    AVG(
                        TIMESTAMPDIFF(
                            MINUTE,
                            arrival_time,
                            completion_time
                        )
                    ) AS avg_processing
                FROM procurement
                WHERE arrival_time IS NOT NULL
                AND completion_time IS NOT NULL
            """)

            avg_result = cursor.fetchone()

            avg_processing = avg_result["avg_processing"]

            if avg_processing is None:
                avg_processing = 5.0

            estimated_wait = ahead * float(avg_processing)

            expected_turn = datetime.now() + timedelta(
                minutes=estimated_wait
            )

            print("\n" + "-" * 60)

            print("TODAY'S PROCUREMENT")

            print("Your token          :", booking["token_number"])
            print("Ahead of you        :", ahead)

            print(
                "Average processing  :",
                round(avg_processing, 2),
                "min"
            )

            print(
                "Estimated waiting   :",
                round(estimated_wait),
                "minutes"
            )

            print(
                "Expected turn       :",
                expected_turn.strftime("%I:%M %p")
            )

        print("\nPROCUREMENT STATUS")

        stages = [
            "Slot Booked",
            "Farmer Arrived",
            "Quality Inspection",
            "Quantity Verified",
            "Payment Processing",
            "Payment Completed"
        ]

        current_status = booking["status"]

        if current_status == "Cancelled":

            print("❌ Procurement Cancelled")
            return

        current_index = stages.index(current_status)

        for index, stage in enumerate(stages):

            if index <= current_index:

                symbol = "🟢"

            else:

                symbol = "⚪"

            print(symbol, stage)

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Move a booking through the procurement process
def update_procurement_status():

    print("\n" + "=" * 65)
    print("              UPDATE PROCUREMENT STATUS")
    print("=" * 65)

    procurement_id = input(
        "Enter Procurement ID: "
    ).strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                booking_id,
                farmer_id,
                status,
                token_number
            FROM bookings
            WHERE procurement_id = %s
        """, (procurement_id,))

        booking = cursor.fetchone()

        if booking is None:

            print("Procurement not found.")
            return

        print("\nCurrent status:", booking["status"])

        print("\nAvailable actions:")

        print("1. Farmer Arrived")
        print("2. Quality Inspection")
        print("3. Quantity Verified")
        print("4. Payment Processing")
        print("5. Payment Completed")
        print("6. Cancel Booking")

        choice = input(
            "\nEnter choice: "
        ).strip()

        status_map = {
            "1": "Farmer Arrived",
            "2": "Quality Inspection",
            "3": "Quantity Verified",
            "4": "Payment Processing",
            "5": "Payment Completed",
            "6": "Cancelled"
        }

        if choice not in status_map:

            print("Invalid choice.")
            return

        new_status = status_map[choice]

        if new_status == "Farmer Arrived":

            cursor.execute("""
                UPDATE bookings
                SET status = 'Farmer Arrived'
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                UPDATE procurement
                SET arrival_time = NOW()
                WHERE procurement_id = %s
            """, (procurement_id,))

        elif new_status == "Quality Inspection":

            cursor.execute("""
                UPDATE bookings
                SET status = 'Quality Inspection'
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                UPDATE procurement
                SET inspection_start = NOW()
                WHERE procurement_id = %s
            """, (procurement_id,))

        elif new_status == "Quantity Verified":

            while True:

                try:

                    verified_quantity = float(
                        input(
                            "Enter verified quantity (kg): "
                        )
                    )

                    if verified_quantity <= 0:

                        print(
                            "Quantity must be greater than 0."
                        )

                        continue

                    break

                except ValueError:

                    print(
                        "Enter a valid quantity."
                    )

            cursor.execute("""
                UPDATE bookings
                SET status = 'Quantity Verified'
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                UPDATE procurement
                SET
                    inspection_end = NOW(),
                    verified_quantity = %s
                WHERE procurement_id = %s
            """, (
                verified_quantity,
                procurement_id
            ))

        elif new_status == "Payment Processing":

            cursor.execute("""
                UPDATE bookings
                SET status = 'Payment Processing'
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                UPDATE procurement
                SET payment_status = 'Processing'
                WHERE procurement_id = %s
            """, (procurement_id,))

        elif new_status == "Payment Completed":

            cursor.execute("""
                UPDATE bookings
                SET status = 'Payment Completed'
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                UPDATE procurement
                SET
                    payment_status = 'Completed',
                    completion_time = NOW()
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                SELECT farmer_id
                FROM bookings
                WHERE procurement_id = %s
            """, (procurement_id,))

            farmer_id = cursor.fetchone()["farmer_id"]

            message = (
                f"Procurement {procurement_id} "
                f"has been completed. "
                f"Payment status: Completed."
            )

            cursor.execute("""
                INSERT INTO notifications
                (
                    farmer_id,
                    procurement_id,
                    message,
                    notification_type,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'Procurement Completed',
                    'Sent'
                )
            """, (
                farmer_id,
                procurement_id,
                message
            ))

        elif new_status == "Cancelled":

            cursor.execute("""
                UPDATE bookings
                SET status = 'Cancelled'
                WHERE procurement_id = %s
            """, (procurement_id,))

            cursor.execute("""
                SELECT slot_id
                FROM bookings
                WHERE procurement_id = %s
            """, (procurement_id,))

            slot = cursor.fetchone()

            if slot:

                cursor.execute("""
                    UPDATE slots
                    SET
                        booked_farmer =
                            GREATEST(booked_farmer - 1, 0),
                        status = 'Available'
                    WHERE slot_id = %s
                """, (slot["slot_id"],))

        conn.commit()

        print(
            "\nProcurement status updated to:",
            new_status
        )

    except Error as e:

        if conn:
            conn.rollback()

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Call the next farmer
def call_next_farmer():

    print("\n" + "=" * 60)
    print("                  CALL NEXT FARMER")
    print("=" * 60)

    try:

        center_id = int(
            input("Enter Procurement Center ID: ")
        )

    except ValueError:

        print("Invalid center ID.")
        return

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = date.today()

        cursor.execute("""
            SELECT
                b.procurement_id,
                b.token_number,
                b.farmer_id,
                f.name
            FROM bookings b
            JOIN farmers f
                ON b.farmer_id = f.farmer_id
            WHERE b.center_id = %s
            AND b.booking_date = %s
            AND b.status = 'Slot Booked'
            ORDER BY b.token_number
            LIMIT 1
        """, (
            center_id,
            today
        ))

        farmer = cursor.fetchone()

        if farmer is None:

            print("No waiting farmers.")
            return

        cursor.execute("""
            UPDATE bookings
            SET status = 'Farmer Arrived'
            WHERE procurement_id = %s
        """, (
            farmer["procurement_id"],
        ))

        cursor.execute("""
            UPDATE procurement
            SET arrival_time = NOW()
            WHERE procurement_id = %s
        """, (
            farmer["procurement_id"],
        ))

        message = (
            f"Token {farmer['token_number']} "
            f"is now being served. "
            f"Please proceed to the procurement counter."
        )

        cursor.execute("""
            INSERT INTO notifications
            (
                farmer_id,
                procurement_id,
                message,
                notification_type,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'Turn Reached',
                'Sent'
            )
        """, (
            farmer["farmer_id"],
            farmer["procurement_id"],
            message
        ))

        conn.commit()

        print("\nNEXT FARMER")

        print(
            "Token:",
            farmer["token_number"]
        )

        print(
            "Farmer:",
            farmer["name"]
        )

        print(
            "Procurement ID:",
            farmer["procurement_id"]
        )

        print("\nNotification sent.")

    except Error as e:

        if conn:
            conn.rollback()

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Show complete procurement details
def view_procurement_details():

    print("\n" + "=" * 65)
    print("                 PROCUREMENT DETAILS")
    print("=" * 65)

    procurement_id = input(
        "Enter Procurement ID: "
    ).strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                b.procurement_id,
                f.name AS farmer_name,
                f.mobile,
                f.village,
                pc.center_name,
                pc.location,
                b.expected_quantity,
                p.verified_quantity,
                b.token_number,
                b.booking_date,
                b.status,
                p.arrival_time,
                p.inspection_start,
                p.inspection_end,
                p.payment_status,
                p.completion_time
            FROM bookings b

            JOIN farmers f
                ON b.farmer_id = f.farmer_id

            JOIN procurement_centers pc
                ON b.center_id = pc.center_id

            JOIN procurement p
                ON b.procurement_id = p.procurement_id

            WHERE b.procurement_id = %s
        """, (procurement_id,))

        record = cursor.fetchone()

        if record is None:

            print("Procurement record not found.")
            return

        print("\nFarmer Name       :", record["farmer_name"])
        print("Mobile            :", record["mobile"])
        print("Village           :", record["village"])

        print("\nProcurement ID    :", record["procurement_id"])
        print("Center            :", record["center_name"])
        print("Location          :", record["location"])

        print("\nExpected Quantity :", record["expected_quantity"], "kg")
        print("Verified Quantity :", record["verified_quantity"], "kg")

        print("Token Number      :", record["token_number"])
        print("Booking Date      :", record["booking_date"])

        print("\nCurrent Status    :", record["status"])

        print("\nArrival Time      :", record["arrival_time"])
        print("Inspection Start  :", record["inspection_start"])
        print("Inspection End    :", record["inspection_end"])

        print("Payment Status    :", record["payment_status"])
        print("Completion Time   :", record["completion_time"])

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Update farmer information
def update_farmer():

    print("\n" + "=" * 60)
    print("                 UPDATE FARMER")
    print("=" * 60)

    try:

        farmer_id = int(
            input("Enter Farmer ID: ")
        )

    except ValueError:

        print("Invalid Farmer ID.")
        return

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                name,
                mobile,
                registration_id,
                village
            FROM farmers
            WHERE farmer_id = %s
        """, (farmer_id,))

        farmer = cursor.fetchone()

        if farmer is None:

            print("Farmer not found.")
            return

        print("\nCurrent Details")

        print("Name            :", farmer[0])
        print("Mobile          :", farmer[1])
        print("Registration ID :", farmer[2])
        print("Village         :", farmer[3])

        while True:

            new_mobile = input(
                "\nEnter new mobile "
                "(Enter to keep current): "
            ).strip()

            if new_mobile == "":
                new_mobile = farmer[1]
                break

            if new_mobile.isdigit() and len(new_mobile) == 10:
                break

            print(
                "Invalid mobile number."
            )

        new_village = input(
            "Enter new village "
            "(Enter to keep current): "
        ).strip()

        if new_village == "":
            new_village = farmer[3]

        cursor.execute("""
            UPDATE farmers
            SET mobile = %s,
                village = %s
            WHERE farmer_id = %s
        """, (
            new_mobile,
            new_village,
            farmer_id
        ))

        conn.commit()

        print("\nFarmer details updated successfully!")

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Search farmers
def search_farmer():

    print("\n" + "=" * 60)
    print("                    SEARCH FARMER")
    print("=" * 60)

    search_value = input(
        "Enter farmer name / mobile / registration ID: "
    ).strip()

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                farmer_id,
                name,
                mobile,
                registration_id,
                village
            FROM farmers
            WHERE name LIKE %s
            OR mobile = %s
            OR registration_id = %s
        """

        cursor.execute(
            query,
            (
                "%" + search_value + "%",
                search_value,
                search_value
            )
        )

        farmers = cursor.fetchall()

        if not farmers:

            print("\nNo farmer found.")
            return

        print(
            "\nID | Name | Mobile | Registration ID | Village"
        )

        print("-" * 80)

        for farmer in farmers:

            print(
                farmer[0], "|",
                farmer[1], "|",
                farmer[2], "|",
                farmer[3], "|",
                farmer[4]
            )

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Basic procurement statistics
def analytics():

    print("\n" + "=" * 70)
    print("                  PROCUREMENT ANALYTICS")
    print("=" * 70)

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = date.today()

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM farmers
        """)

        total_farmers = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE booking_date = %s
        """, (today,))

        todays_bookings = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE booking_date = %s
            AND status = 'Payment Completed'
        """, (today,))

        processed = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE booking_date = %s
            AND status = 'Slot Booked'
        """, (today,))

        waiting = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE booking_date = %s
            AND status = 'Payment Processing'
        """, (today,))

        payment_processing = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COALESCE(SUM(expected_quantity), 0) AS quantity
            FROM bookings
            WHERE booking_date = %s
        """, (today,))

        expected_quantity = cursor.fetchone()["quantity"]

        cursor.execute("""
            SELECT COALESCE(SUM(p.verified_quantity), 0) AS quantity
            FROM procurement p
            JOIN bookings b
                ON p.booking_id = b.booking_id
            WHERE b.booking_date = %s
        """, (today,))

        verified_quantity = cursor.fetchone()["quantity"]

        cursor.execute("""
            SELECT AVG(
                TIMESTAMPDIFF(
                    MINUTE,
                    arrival_time,
                    completion_time
                )
            ) AS average_time
            FROM procurement
            WHERE arrival_time IS NOT NULL
            AND completion_time IS NOT NULL
        """)

        avg_time = cursor.fetchone()["average_time"]

        if avg_time is None:
            avg_time = 0

        print("\nTODAY'S OVERVIEW")

        print("-" * 70)

        print(
            "Total registered farmers :",
            total_farmers
        )

        print(
            "Today's bookings         :",
            todays_bookings
        )

        print(
            "Farmers processed        :",
            processed
        )

        print(
            "Farmers waiting          :",
            waiting
        )

        print(
            "Payment processing       :",
            payment_processing
        )

        print(
            "Expected quantity        :",
            expected_quantity,
            "kg"
        )

        print(
            "Verified quantity        :",
            verified_quantity,
            "kg"
        )

        print(
            "Average processing time  :",
            round(avg_time, 2),
            "minutes"
        )

        print("\nCENTER-WISE WORKLOAD")

        cursor.execute("""
            SELECT
                pc.center_name,
                COUNT(b.booking_id) AS farmers,
                COALESCE(
                    SUM(b.expected_quantity), 0
                ) AS quantity
            FROM procurement_centers pc

            LEFT JOIN bookings b
                ON pc.center_id = b.center_id
                AND b.booking_date = %s

            GROUP BY
                pc.center_id,
                pc.center_name

            ORDER BY farmers DESC
        """, (today,))

        centers = cursor.fetchall()

        print(
            "\nCenter | Farmers | Expected Quantity"
        )

        print("-" * 60)

        for center in centers:

            print(
                center["center_name"], "|",
                center["farmers"], "|",
                center["quantity"], "kg"
            )

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Notification history
def view_notifications():

    print("\n" + "=" * 70)
    print("                  NOTIFICATION LOG")
    print("=" * 70)

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                notification_id,
                procurement_id,
                message,
                notification_type,
                status,
                created_at
            FROM notifications
            ORDER BY created_at DESC
            LIMIT 20
        """)

        notifications = cursor.fetchall()

        if not notifications:

            print("No notifications found.")
            return

        for notification in notifications:

            print("\nNotification ID:",
                  notification[0])

            print(
                "Procurement ID:",
                notification[1]
            )

            print(
                "Type:",
                notification[3]
            )

            print(
                "Status:",
                notification[4]
            )

            print(
                "Message:",
                notification[2]
            )

            print(
                "Time:",
                notification[5]
            )

            print("-" * 70)

    except Error as e:

        print("Database error:", e)

    finally:

        close_connection(conn, cursor)

# Main menu
def main():

    while True:

        print("\n")
        print("=" * 65)
        print("       PROCUREMENT QUEUE & SLOT MANAGEMENT SYSTEM")
        print("=" * 65)

        print("\nFARMER SERVICES")
        print("1. Register Farmer")
        print("2. View Procurement Centers")
        print("3. Book Procurement Slot")
        print("4. Track Queue")
        print("5. View Procurement Details")
        print("6. Update Farmer Details")
        print("7. Search Farmer")

        print("\nOFFICER SERVICES")
        print("8. View Today's Live Queue")
        print("9. Call Next Farmer")
        print("10. Update Procurement Status")

        print("\nADMIN SERVICES")
        print("11. View Analytics")
        print("12. View Notification Log")

        print("\n13. Exit")

        choice = input(
            "\nEnter your choice: "
        ).strip()

        if choice == "1":

            register_farmer()

        elif choice == "2":

            view_centers()

        elif choice == "3":

            book_procurement_slot()

        elif choice == "4":

            track_queue()

        elif choice == "5":

            view_procurement_details()

        elif choice == "6":

            update_farmer()

        elif choice == "7":

            search_farmer()

        elif choice == "8":

            view_live_queue()

        elif choice == "9":

            call_next_farmer()

        elif choice == "10":

            update_procurement_status()

        elif choice == "11":

            analytics()

        elif choice == "12":

            view_notifications()

        elif choice == "13":

            print(
                "\nThank you for using the "
                "Procurement Queue & Slot Management System."
            )

            break

        else:

            print(
                "\nInvalid choice. Please try again."
            )

if __name__ == "__main__":
    main()
