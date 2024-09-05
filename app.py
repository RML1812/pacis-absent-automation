import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
import json
import pandas as pd
import threading
import os
from datetime import datetime, timedelta
from utils import config, absent, generate_schedule, abort

class AutoAbsent(BoxLayout):
    def __init__(self, **kwargs):
        super(AutoAbsent, self).__init__(**kwargs)
        self.orientation = 'vertical'

        # Create layout for config button
        self.config_layout = BoxLayout(size_hint_y=None, height=50)
        self.add_widget(self.config_layout)

        # Config button
        self.config_button = Button(text="Config", on_press=self.show_config_popup)
        self.config_layout.add_widget(self.config_button)

        # Create layout for reload button
        self.reload_layout = BoxLayout(size_hint_y=None, height=50)
        self.add_widget(self.reload_layout)

        # Reload button
        self.reload_button = Button(text="Reload CSV", on_press=self.reload_csv)
        self.reload_layout.add_widget(self.reload_button)

        # Create grid layout for the CSV content
        self.csv_grid = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.csv_grid)

        # Create layout for bottom buttons
        self.button_layout = BoxLayout(size_hint_y=None, height=50)
        self.add_widget(self.button_layout)

        # Buttons for schedule functionality
        self.generate_button = Button(text="Generate Schedule", on_press=self.run_generate_schedule)
        self.button_layout.add_widget(self.generate_button)

        self.run_button = Button(text="Run Schedule", on_press=self.run_schedule)
        self.button_layout.add_widget(self.run_button)

        self.stop_button = Button(text="Stop Schedule", on_press=self.stop_schedule)
        self.stop_button.disabled = True
        self.button_layout.add_widget(self.stop_button)

        # Abort button
        self.abort_button = Button(text="Abort Attendance", on_press=self.abort_attendance)
        self.abort_button.disabled = True
        self.button_layout.add_widget(self.abort_button)

        # Create text area for logging (view only)
        self.log_text_area = TextInput(size_hint_y=None, height=150, readonly=True, multiline=True)
        self.add_widget(self.log_text_area)

        # Create a label for successfull absent
        self.recent_absent_label = Label(text="", size_hint_y=None, height=40)
        self.add_widget(self.recent_absent_label)

        # Create a label for the countdown display
        self.countdown_label = Label(text="", size_hint_y=None, height=40)
        self.add_widget(self.countdown_label)

        # Store csv data
        self.csv_data = None

        # Check if config.json and schedule.csv exists
        self.check_file()

    def log_message(self, message):
        # Get the current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Schedule the actual log update on the main thread
        Clock.schedule_once(lambda dt: self._log_message(f"[{timestamp}] {message}\n"))

    def _log_message(self, formatted_message):
        # This method updates the log_text_area, and it should be called only from the main thread
        self.log_text_area.text += formatted_message

    def check_file(self):
        # Check if config file exists
        if not os.path.exists("config.json"):
            self.disable_buttons()
            self.log_message("Configuration file not found. Please configure the settings first.")
            return
        else:
            self.load_config_data()
        
        # Check if schedule.csv exists
        if not os.path.exists("schedule.csv"):
            self.disable_buttons()
            self.display_no_schedule_message()

            if os.path.exists("config.json"):
                self.generate_button.disabled = False
                
        else:
            self.load_csv_data()

        # Check if config.json and schedule.csv exists
        if os.path.exists("schedule.csv") and os.path.exists("config.json"):
            self.enable_buttons()

    def load_config_data(self):
        try:
            # Check if the config file exists
            if os.path.exists("config.json"):
                with open("config.json", "r") as config_file:
                    config_data = json.load(config_file)

                # Extract the data
                username = config_data.get("username", "")
                password = config_data.get("password", "")
                browser = config_data.get("browser", "")

                # Call the config function from utils.py
                config(username, password, browser)
                self.log_message("Configuration data loaded successfully.")
            else:
                self.log_message("No configuration file found.")
        except Exception as e:
            self.log_message(f"Error loading configuration data: {str(e)}")

    def show_config_popup(self, instance):
        # Create a popup for the configuration
        config_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Create text inputs for Username and Password
        self.username_input = TextInput(hint_text="Username", multiline=False)
        self.password_input = TextInput(hint_text="Password", multiline=False, password=True)
        
        # Create a dropdown spinner for Installed Browser
        self.browser_spinner = Spinner(text='Select Browser', values=('Chrome', 'Firefox', 'Edge'))
        
        # Add inputs to the layout
        config_layout.add_widget(Label(text="Username"))
        config_layout.add_widget(self.username_input)
        config_layout.add_widget(Label(text="Password"))
        config_layout.add_widget(self.password_input)
        config_layout.add_widget(Label(text="Installed Browser"))
        config_layout.add_widget(self.browser_spinner)
        
        # Save and Cancel buttons
        buttons_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        save_button = Button(text="Save", on_press=self.save_config)
        cancel_button = Button(text="Cancel", on_press=lambda *args: config_popup.dismiss())
        
        buttons_layout.add_widget(save_button)
        buttons_layout.add_widget(cancel_button)
        config_layout.add_widget(buttons_layout)
        
        # Create the popup
        config_popup = Popup(title="Configuration", content=config_layout, size_hint=(0.8, 0.5))
        config_popup.open()

    def save_config(self, instance):
        config_data = {
            "username": self.username_input.text,
            "password": self.password_input.text,
            "browser": self.browser_spinner.text
        }
        
        # Save the configuration to a file
        with open("config.json", "w") as config_file:
            json.dump(config_data, config_file)
        
        self.log_message("Configuration saved.")
        self.check_file()

    def display_no_schedule_message(self):
        self.csv_grid.clear_widgets()
        label = Label(text="No schedule generated yet", font_size=32, halign="center")
        self.csv_grid.add_widget(label)
        self.log_message("No schedule file found.")

    def disable_buttons(self):
        self.reload_button.disabled = True
        self.run_button.disabled = True
        self.stop_button.disabled = True
        self.generate_button.disabled = True
        self.config_button.disabled = False

    def enable_buttons(self):
        self.reload_button.disabled = False
        self.run_button.disabled = False
        self.stop_button.disabled = True
        self.generate_button.disabled = False

    def load_csv_data(self):
        self.csv_grid.clear_widgets()
        self.csv_data = pd.read_csv("schedule.csv")

        # Add an "Action" column
        self.csv_grid.cols = len(self.csv_data.columns) + 1  # Extra column for the action buttons
        self.csv_grid.bind(minimum_height=self.csv_grid.setter('height'))

        # Display the CSV headers with borders
        for header in self.csv_data.columns:
            label = Label(text=header, size_hint_y=None, height=40)
            self.add_border(label)
            self.csv_grid.add_widget(label)

        # Add header for the new "Action" column
        action_header = Label(text="Action", size_hint_y=None, height=40)
        self.add_border(action_header)
        self.csv_grid.add_widget(action_header)

        # Display the CSV content
        for index, row in self.csv_data.iterrows():
            for i, col in enumerate(self.csv_data.columns):
                if i == 0:
                    # First column (No) is not editable, display as Label
                    label = Label(text=str(row[col]), size_hint_y=None, height=40)
                    self.add_border(label)
                    self.csv_grid.add_widget(label)
                elif i in [1, 2]:  # Editable columns (2nd and 3rd)
                    cell = TextInput(text=str(row[col]), multiline=False, size_hint_y=None, height=40)
                    cell.bind(text=self.on_text)
                    cell.bind(on_text_validate=self.save_and_sort_csv)
                    cell.row = index  # Store the row index in the widget
                    cell.col = col    # Store the column name in the widget
                    self.add_border(cell)
                    self.csv_grid.add_widget(cell)
                else:
                    # Other columns are not editable, display as Label
                    label = Label(text=str(row[col]), size_hint_y=None, height=40)
                    self.add_border(label)
                    self.csv_grid.add_widget(label)

            # Add "Delete" and "Run Now" buttons for each row in the "Action" column
            action_layout = BoxLayout(size_hint_y=None, height=40)

            # Delete button
            delete_button = Button(text="Delete", on_press=lambda btn, idx=index: self.delete_row(idx))
            action_layout.add_widget(delete_button)

            # Run Now button
            run_now_button = Button(text="Run Now", on_press=lambda btn, id=row['ID Matkul']: self.run_now(id))
            action_layout.add_widget(run_now_button)

            self.add_border(action_layout)
            self.csv_grid.add_widget(action_layout)

        self.log_message("CSV file loaded with action buttons from schedule.csv")

    def delete_row(self, index):
        # Remove the row at the given index
        self.csv_data.drop(index, inplace=True)

        # Reset the index of the DataFrame after deleting the row
        self.csv_data.reset_index(drop=True, inplace=True)

        # Rewrite the "No" column based on the new order
        self.csv_data['No'] = range(1, len(self.csv_data) + 1)

        # Save the updated CSV
        self.csv_data.to_csv("schedule.csv", index=False)

        # Refresh the grid display after deletion
        self.load_csv_data()

        self.log_message(f"Row {index + 1} deleted successfully.")

    def run_now(self, id_matkul):
        # Enable the abort button
        self.abort_button.disabled = False
        
        # Define a function that will run in the thread and handle the attendance process
        def attendance_task():
            result = absent(self, id_matkul)  # Run the absent function and store the result (True/False)
            # Schedule a UI update back in the main thread after the thread completes
            if result:
                Clock.schedule_once(lambda dt: self.update_attendance_status(id_matkul, success=True))
                self.abort_button.disabled = True
            else:
                Clock.schedule_once(lambda dt: self.update_attendance_status(id_matkul, success=False))
                self.abort_button.disabled = True
        
        # Start the attendance task in a separate thread
        threading.Thread(target=attendance_task).start()

    def update_attendance_status(self, id_matkul, success):
        # Update UI based on the result of the attendance process
        if success:
            self.recent_absent_label.text = f"Recent Successful Absent: {id_matkul}"
        else:
            self.log_message(f"Absent failed or aborted for Matkul ID {id_matkul}")

    def add_border(self, widget):
        with widget.canvas.after:
            Color(1, 1, 1, 1)  # White color for the border
            Line(rectangle=(widget.x, widget.y, widget.width, widget.height), width=1)
            widget.bind(pos=self.update_border, size=self.update_border)

    def update_border(self, instance, value):
        instance.canvas.after.clear()
        with instance.canvas.after:
            Color(1, 1, 1, 1)  # White color for the border
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)

    def save_and_sort_csv(self, instance):
        # Update the DataFrame with the new value
        self.csv_data.at[instance.row, instance.col] = instance.text

        # Convert the 'Jam Absen' to a sortable format if it's not already sorted correctly
        self.csv_data['Jam Absen'] = pd.to_datetime(self.csv_data['Jam Absen'], format='%H:%M').dt.strftime('%H:%M')

        # Define the order of days in the week for sorting
        day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        self.csv_data['Hari'] = pd.Categorical(self.csv_data['Hari'], categories=day_order, ordered=True)

        # Sort the DataFrame by 'Hari' and 'Jam Absen'
        self.csv_data.sort_values(by=['Hari', 'Jam Absen'], inplace=True)

        # Rewrite the 'No' column based on the new order
        self.csv_data['No'] = range(1, len(self.csv_data) + 1)

        # Save the updated and sorted DataFrame to the CSV
        self.csv_data.to_csv("schedule.csv", index=False)

        # Refresh the grid display after sorting
        self.load_csv_data()

        self.log_message("CSV file sorted, 'No' column updated, and saved to schedule.csv")

    def reload_csv(self, instance):
        # Reload the CSV file
        self.load_csv_data()
        self.log_message("CSV file reloaded from schedule.csv")

    def on_text(self, instance, value):
        # This function can be used to handle real-time changes if needed
        pass

    def run_generate_schedule(self, instance):
        # Define a function to run after the generate_schedule is done
        def schedule_callback(*args):
            # This will run in the main thread
            self.check_file()

        # This function will run in a separate thread
        def target_function():
            # Call the generate_schedule function from utils.py
            generate_schedule(self)
            # Schedule check_file to run on the main thread after the thread finishes
            Clock.schedule_once(schedule_callback)

        # Start the thread
        threading.Thread(target=target_function).start()

    def run_schedule(self, instance):
        self.log_message("Schedule is now running.")
        
        # Disable all buttons except the stop and abort buttons
        self.disable_buttons()
        self.stop_button.disabled = False
        self.abort_button.disabled = True  # Initially disabled

        # Reset the recent absent label
        self.recent_absent_label.text = "Recent Successful Absent: none"

        # Start schedule and update the countdown label with the nearest schedule
        Clock.schedule_interval(self.update_countdown, 1)

    def stop_schedule(self, instance):
        # Clear the countdown label
        self.countdown_label.text = ""
        self.log_message("Schedule stopped.")

        # Clear the recent absent label
        self.recent_absent_label.text = ""

        # Stop schedule and unschedule the update_countdown method to stop the countdown updates
        Clock.unschedule(self.update_countdown)

        # Re-enable all buttons
        self.enable_buttons()
        self.stop_button.disabled = True

    def update_countdown(self, dt):
        # Get the current time and day
        now = datetime.now()
        nearest_time = None
        next_matkul = None
        next_id = None

        # Define the order of days in the week (in Indonesian)
        day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

        # Create a mapping from English day names to Indonesian day names
        day_mapping = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu"
        }

        # Get today's day in Indonesian
        today_indonesian = day_mapping[now.strftime('%A')]
        today_index = day_order.index(today_indonesian)

        for index, row in self.csv_data.iterrows():
            matkul_time = row['Jam Absen']
            matkul_day = row['Hari']
            matkul_datetime = datetime.strptime(matkul_time, '%H:%M')

            # Calculate the datetime for the matkul
            matkul_day_index = day_order.index(matkul_day)

            # If the matkul is on the same day but in the future
            if matkul_day_index == today_index and matkul_datetime.time() > now.time():
                matkul_datetime = datetime.combine(now.date(), matkul_datetime.time())

            # If the matkul is on a future day
            elif matkul_day_index > today_index:
                days_ahead = matkul_day_index - today_index
                matkul_datetime = datetime.combine(now.date() + timedelta(days=days_ahead), matkul_datetime.time())

            # If the matkul is on a past day (i.e., next week)
            elif matkul_day_index < today_index or (matkul_day_index == today_index and matkul_datetime.time() < now.time()):
                days_ahead = (7 - today_index) + matkul_day_index
                matkul_datetime = datetime.combine(now.date() + timedelta(days=days_ahead), matkul_datetime.time())

            # Update nearest_time if this matkul is closer than the current nearest_time
            if nearest_time is None or matkul_datetime < nearest_time:
                nearest_time = matkul_datetime
                next_matkul = row['Matkul']
                next_id = row['ID Matkul']

        if nearest_time is not None:
            countdown = nearest_time - now
            self.countdown_label.text = f"Next Matkul: {next_matkul} (ID: {next_id}), {nearest_time.strftime('%A')} {nearest_time.strftime('%H:%M')} - Countdown: {str(countdown).split('.')[0]}"

            # When the countdown is within a small threshold (e.g., 1 second) before zero
            if timedelta(seconds=-1) < countdown < timedelta(seconds=1):
                self.countdown_label.text = f"Running attend absent for matkul {next_matkul} (ID: {next_id})"
                self.run_now(next_id)

        else:
            self.countdown_label.text = "No more schedules found."

    def abort_attendance(self, instance):
        threading.Thread(target=abort, args=(self,)).start()  # Call the abort function
        self.abort_button.disabled = True  # Disable abort button after abort


class AutoAbsentApp(App):
    def build(self):
        # Set the window icon before building the UI
        Window.set_icon('icon.png')
        
        return AutoAbsent()

if __name__ == "__main__":
    AutoAbsentApp().run()