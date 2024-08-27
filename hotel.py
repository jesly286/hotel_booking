import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import random
import string

class DatabaseConnection:
    def __init__(self, host, user, password, database):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='12345',
                database='hotel_booking'
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            self.connection = None

    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection is closed")

    def create_tables(self):
        try:
            cursor = self.connection.cursor()

            # Create Rooms table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rooms (
                room_id INT AUTO_INCREMENT PRIMARY KEY,
                category ENUM('Single', 'Double', 'Suite', 'Convention Hall', 'Ballroom') NOT NULL,
                room_no VARCHAR(10) NOT NULL,
                price_per_day DECIMAL(10, 2),
                price_per_hour DECIMAL(10, 2),
                is_occupied BOOLEAN DEFAULT FALSE
            );
            """)

            # Create Customers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Customers (
                customer_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(15) NOT NULL,
                address TEXT
            );
            """)

            # Create Bookings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Bookings (
                booking_id VARCHAR(7) PRIMARY KEY,
                customer_id INT NOT NULL,
                room_id INT NOT NULL,
                date_of_booking DATE NOT NULL,
                date_of_occupancy DATE NOT NULL,
                no_of_days INT,
                no_of_hours INT,
                advance_received DECIMAL(10, 2),
                tax DECIMAL(10, 2),
                housekeeping_charges DECIMAL(10, 2),
                misc_charges DECIMAL(10, 2),
                total_amount DECIMAL(10, 2),
                FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
                FOREIGN KEY (room_id) REFERENCES Rooms(room_id)
            );
            """)

            # Create Admins table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Admins (
                admin_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                phone VARCHAR(15),
                role ENUM('Manager', 'Staff') DEFAULT 'Staff',
                date_joined DATE NOT NULL,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            self.connection.commit()
            print("Tables created successfully")
        except Error as e:
            print(f"Error while creating tables: {e}")

from decimal import Decimal

class Booking:
    def __init__(self, booking_id, customer_id, room_id, date_of_booking, date_of_occupancy, no_of_days=None, no_of_hours=None, advance_received=0):
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.room_id = room_id
        self.date_of_booking = date_of_booking
        self.date_of_occupancy = date_of_occupancy
        self.no_of_days = no_of_days
        self.no_of_hours = no_of_hours
        self.advance_received = Decimal(advance_received)  # Convert advance_received to Decimal
        self.tax = Decimal(0.0)
        self.housekeeping_charges = Decimal(100.0)
        self.misc_charges = Decimal(50.0)
        self.total_amount = Decimal(0.0)

    def calculate_total_amount(self, room_price, tax_rate):
        room_price = Decimal(room_price)  # Ensure room_price is Decimal
        tax_rate = Decimal(tax_rate)  # Ensure tax_rate is Decimal

        if self.no_of_days:
            base_amount = Decimal(self.no_of_days) * room_price
        else:
            base_amount = Decimal(self.no_of_hours) * room_price

        self.tax = base_amount * tax_rate
        self.total_amount = base_amount + self.tax + self.housekeeping_charges + self.misc_charges - self.advance_received

    @staticmethod
    def generate_booking_id():
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        digits = ''.join(random.choices(string.digits, k=5))
        return letters + digits

    @staticmethod
    def validate_date_input(date_string):
        try:
            valid_date = datetime.strptime(date_string, "%Y-%m-%d").date()
            return valid_date
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return None

class RoomBookingSystem:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def list_occupied_rooms_next_two_days(self):
        try:
            today = datetime.today().date()
            next_two_days = today + timedelta(days=2)
            query = """
            SELECT Rooms.room_no, Rooms.category, Bookings.date_of_occupancy, 
                   COALESCE(Bookings.no_of_days, 0), COALESCE(Bookings.no_of_hours, 0) 
            FROM Rooms 
            JOIN Bookings ON Rooms.room_id = Bookings.room_id 
            WHERE Bookings.date_of_occupancy BETWEEN %s AND %s;
            """
            cursor = self.db_connection.connection.cursor()
            cursor.execute(query, (today, next_two_days))
            occupied_rooms = cursor.fetchall()

            if occupied_rooms:
                print(f"Rooms occupied from {today} to {next_two_days}:")
                for room in occupied_rooms:
                    duration = f"{room[3]} days" if room[3] > 0 else f"{room[4]} hours"
                    print(f"Room No: {room[0]}, Category: {room[1]}, Occupied from: {room[2]}, Duration: {duration}")
            else:
                print(f"No rooms are occupied from {today} to {next_two_days}.")
        except Error as e:
            print(f"Error fetching occupied rooms: {e}")

    def display_rooms_by_category(self, category):
        try:
            query = "SELECT room_no, price_per_day, price_per_hour FROM Rooms WHERE category = %s"
            cursor = self.db_connection.connection.cursor()
            cursor.execute(query, (category,))
            rooms = cursor.fetchall()
            if rooms:
                print(f"{category} Rooms:")
                for room in rooms:
                    if category in ['Convention Hall', 'Ballroom']:
                        print(f"Room No: {room[0]}, Rate per hour: {room[2]}")
                    else:
                        print(f"Room No: {room[0]}, Rate per day: {room[1]}")
            else:
                print(f"No rooms available for category: {category}")
        except Error as e:
            print(f"Error fetching rooms by category: {e}")

    def list_rooms_by_rate(self):
        try:
            query = "SELECT room_no, category, price_per_day, price_per_hour FROM Rooms ORDER BY price_per_day ASC, price_per_hour ASC"
            cursor = self.db_connection.connection.cursor()
            cursor.execute(query)
            sorted_rooms = cursor.fetchall()

            if sorted_rooms:
                print("Rooms sorted by rate:")
                for room in sorted_rooms:
                    if room[1] in ['Convention Hall', 'Ballroom']:
                        print(f"Room No: {room[0]}, Category: {room[1]}, Rate per hour: {room[3]}")
                    else:
                        print(f"Room No: {room[0]}, Category: {room[1]}, Rate per day: {room[2]}")
            else:
                print("No rooms available in the database.")
        except Error as e:
            print(f"Error fetching room data: {e}")

    def search_room_by_booking_id(self, booking_id):
        try:
            query = """
            SELECT Rooms.room_no, Customers.first_name, Customers.last_name, 
                   Bookings.date_of_booking, Bookings.date_of_occupancy, 
                   COALESCE(Bookings.no_of_days, 0), COALESCE(Bookings.no_of_hours, 0)
            FROM Bookings
            JOIN Rooms ON Bookings.room_id = Rooms.room_id
            JOIN Customers ON Bookings.customer_id = Customers.customer_id
            WHERE Bookings.booking_id = %s;
            """
            cursor = self.db_connection.connection.cursor()
            cursor.execute(query, (booking_id,))
            booking_details = cursor.fetchone()

            if booking_details:
                duration = f"{booking_details[5]} days" if booking_details[5] > 0 else f"{booking_details[6]} hours"
                print(f"Booking ID: {booking_id}")
                print(f"Room No: {booking_details[0]}")
                print(f"Customer Name: {booking_details[1]} {booking_details[2]}")
                print(f"Date of Booking: {booking_details[3]}")
                print(f"Date of Occupancy: {booking_details[4]}")
                print(f"Duration: {duration}")
            else:
                print(f"No details found for Booking ID: {booking_id}")
        except Error as e:
            print(f"Error fetching booking details: {e}")

    def display_unoccupied_rooms(self):
        try:
            query = "SELECT room_no, category FROM Rooms WHERE is_occupied = FALSE"
            cursor = self.db_connection.connection.cursor()
            cursor.execute(query)
            unoccupied_rooms = cursor.fetchall()

            if unoccupied_rooms:
                print("Unoccupied Rooms:")
                for room in unoccupied_rooms:
                    print(f"Room No: {room[0]}, Category: {room[1]}")
            else:
                print("All rooms are currently occupied.")
        except Error as e:
            print(f"Error fetching unoccupied rooms: {e}")

    def book_room(self, customer_id, room_id, date_of_occupancy, no_of_days=None, no_of_hours=None, advance_received=0):
        try:
            # Fetch room price
            cursor = self.db_connection.connection.cursor()
            cursor.execute("SELECT price_per_day, price_per_hour FROM Rooms WHERE room_id = %s", (room_id,))
            room_data = cursor.fetchone()

            if not room_data:
                print(f"Room ID {room_id} does not exist.")
                return

            room_price = room_data[0] if no_of_days else room_data[1]
            booking_id = Booking.generate_booking_id()
            date_of_booking = datetime.today().date()

            booking = Booking(
                booking_id=booking_id,
                customer_id=customer_id,
                room_id=room_id,
                date_of_booking=date_of_booking,
                date_of_occupancy=date_of_occupancy,
                no_of_days=no_of_days,
                no_of_hours=no_of_hours,
                advance_received=advance_received
            )
            booking.calculate_total_amount(room_price, tax_rate=0.18)

            # Insert booking data
            insert_query = """
            INSERT INTO Bookings (
                booking_id, customer_id, room_id, date_of_booking, date_of_occupancy,
                no_of_days, no_of_hours, advance_received, tax, housekeeping_charges,
                misc_charges, total_amount
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                booking.booking_id, booking.customer_id, booking.room_id, booking.date_of_booking,
                booking.date_of_occupancy, booking.no_of_days, booking.no_of_hours,
                booking.advance_received, booking.tax, booking.housekeeping_charges,
                booking.misc_charges, booking.total_amount
            ))

            # Mark room as occupied
            cursor.execute("UPDATE Rooms SET is_occupied = TRUE WHERE room_id = %s", (room_id,))
            self.db_connection.connection.commit()
            print(f"Room {room_id} booked successfully. Booking ID: {booking.booking_id}")
        except Error as e:
            print(f"Error during room booking: {e}")

    def menu(self):
        while True:
            print("\n----------------------------------------------------\n"
                       "         Welcome To Room Booking System Menu\n  "
                  "----------------------------------------------------"
                  "")
            print("1. List occupied rooms for the next 2 days")
            print("2. Display rooms by category")
            print("3. List rooms by rate")
            print("4. Search room by booking ID")
            print("5. Display unoccupied rooms")
            print("6. Book a room")
            print("7. Exit")

            choice = input("Enter your choice (1-7): ")

            if choice == '1':
                self.list_occupied_rooms_next_two_days()
            elif choice == '2':
                category = input("Enter room category (Single, Double, Suite, Convention Hall, Ballroom): ")
                if category in ['Single', 'Double', 'Suite', 'Convention Hall', 'Ballroom']:
                    self.display_rooms_by_category(category)
                else:
                    print("Invalid category. Please try again.")
            elif choice == '3':
                self.list_rooms_by_rate()
            elif choice == '4':
                booking_id = input("Enter Booking ID: ")
                self.search_room_by_booking_id(booking_id)
            elif choice == '5':
                self.display_unoccupied_rooms()
            elif choice == '6':
                customer_id = int(input("Enter Customer ID: "))
                room_id = int(input("Enter Room ID: "))
                date_of_occupancy = input("Enter date of occupancy (YYYY-MM-DD): ")
                valid_date = Booking.validate_date_input(date_of_occupancy)
                if not valid_date:
                    continue

                no_of_days = input("Enter number of days (Leave blank if booking hourly): ")
                no_of_hours = input("Enter number of hours (Leave blank if booking daily): ")
                advance_received = float(input("Enter advance received: "))

                if no_of_days:
                    no_of_days = int(no_of_days)
                    no_of_hours = None
                elif no_of_hours:
                    no_of_days = None
                    no_of_hours = int(no_of_hours)
                else:
                    print("You must enter either days or hours for booking.")
                    continue

                self.book_room(customer_id, room_id, valid_date, no_of_days, no_of_hours, advance_received)
            elif choice == '7':
                print("Exiting Room Booking System.")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    db = DatabaseConnection(host='localhost', user='root', password='12345', database='hotel_booking')
    if db.connection:
        db.create_tables()

        booking_system = RoomBookingSystem(db)
        booking_system.menu()

        db.close_connection()

if __name__ == "__main__":
    main()
