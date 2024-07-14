---

# Barber Booking System

## Folder Structure

```
BarberBookingSystem/
├── .venv/                      # Virtual environment folder
├── instance/
│   └── BBS.db                  # SQLite database file
├── static/
│   ├── scissors.png            # Image file
│   └── styles.css              # CSS styles
├── templates/                  # HTML templates
│   ├── add_availability.html
│   ├── add_service.html
│   ├── barber_home.html
│   ├── base.html
│   ├── book_appointment.html
│   ├── calendar.html
│   ├── choose_time.html
│   ├── customer_home.html
│   ├── index.html
│   ├── new_barbershop.html
│   ├── signin.html
│   ├── update_appointment.html
│   ├── update_availability.html
│   ├── update_barbershop.html
│   ├── update_service.html
│   └── view_barbers.html
├── tests/                      # Test cases
│   ├── test_add_availability.py
│   ├── test_add_service.py
│   ├── test_book_appointment_outside_availability.py
│   ├── test_book_barber_appointment.py
│   ├── test_create_barber_account.py
│   ├── test_create_barbershop.py
│   ├── test_create_customer_account.py
│   ├── test_customer_find_barbershop.py
│   ├── test_delete_appointment.py
│   ├── test_find_barbers_in_barbershops.py
│   ├── test_join_barbershop.py
│   └── test_update_appointment_time.py
├── app.py                      # Main application file
├── README.md                   # This README file
└── requirements.txt            # Requirements file
```

## Installation and Testing Instructions

### Prerequisites

- Python 3.7 or higher

### Installation

1. **Create and activate a virtual environment:**

    ```sh
    py -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

2. **Install required packages:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Install PyInstaller:**

    ```sh
    pip install pyinstaller
    ```

### Build the Executable

1. **Run PyInstaller to create the executable:**

    ```sh
    pyinstaller --name Barber_Booking_System --add-data "templates:templates" --add-data "static:static" app.py
    ```

2. **Generate the final executable:**

    ```sh
    pyinstaller Barber_Booking_System.spec
    ```

    - You'll be prompted to press `y` at one point. Press `y` and then `Enter`.

3. **Locate the executable:**

    - Navigate to the `dist` folder.
    - Inside `dist`, find the `Barber_Booking_System` folder.
    - Inside `Barber_Booking_System`, you'll find the Python executable.

### Run the Application

1. **Run the executable:**

    - Click on the Python executable inside the `Barber_Booking_System` folder.
    - A terminal will open.

2. **Access the web application:**

    - In the terminal, you'll see a URL. Ctrl+Click on the URL to open it in your web browser.
    - The website will open up, allowing you to use the Barber Booking System.

---
