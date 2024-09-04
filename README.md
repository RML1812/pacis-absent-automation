# Pacis Absent Automation

Pacis Absent Automation is a tool designed to automate attendance tasks for Universitas Padjadjaran students via the Pacis platform (students.unpad.ac.id). Pacis offers a variety of academic services, including an attendance feature that this application automates based on your academic schedule retrieved directly from the platform.

## Features
- Automates the attendance process using your Pacis schedule
- Allows manual editing of the schedule after generation
- Supports individual or batch attendance execution based on your schedule

## How to Execute the Program

1. **Ensure Python is Installed**  
   Make sure that Python is installed on your machine. You can download it from the [official website](https://www.python.org/).
   
2. **Install the Required Libraries**  
   Install the dependencies by running the following command in your terminal:
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Run the Application**  
   Launch the app by executing:
   ```bash
   python app.py
   ```

## How to Use the App

1. **Configure Your Login and Browser Settings**  
   After launching the app, you’ll need to configure your Pacis username, password, and browser driver settings.
   
2. **Generate Your Schedule**  
   Once your credentials are set, generate your academic schedule from within the app. The schedule will be saved as a `schedule.csv` file.

3. **Edit the Schedule (Optional)**  
   You can either edit the schedule directly within the app or manually edit the `schedule.csv` file to suit your preferences.
   
4. **Run Automated Attendance**  
   Start the automation process by running the schedule. The app will automatically handle attendance for each course based on the schedule.

5. **Manual Attendance Option**  
   If necessary, you can also choose to run attendance for individual courses manually from within the app.

## Contributing

Since this project will be made public, we welcome contributions! Whether you’d like to improve the functionality, add new features, or enhance the user experience, your contributions are greatly appreciated.

Feel free to submit a pull request or raise an issue if you have any ideas or suggestions to help improve the Pacis Absent Automation project.