import firebase_admin
from firebase_admin import credentials, db
import csv

# Firebase setup 
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("Atharva.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://sit225activityweek5-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

ref = db.reference('Atharva/Gyroscope')
snapshot = ref.get()

with open('gyroscope_data.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['timestamp', 'x', 'y', 'z'])

    for item in snapshot.values():
        ts = item['timestamp']
        x = item['data']['x']
        y = item['data']['y']
        z = item['data']['z']
        writer.writerow([ts, x, y, z])

print("Data written to gyroscope_data.csv")
