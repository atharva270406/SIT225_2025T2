import serial
from datetime import datetime

# === SETTINGS ===
PORT = 'COM14'  # Change to your Arduino port
BAUD = 9600  # Match with your Arduino baud rate
OUTPUT_CSV = f"accelerometer_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def main():
    try:
        connection = serial.Serial(PORT, BAUD, timeout=1)
        print(f"Successfully connected to {PORT} at {BAUD} baud rate.")
        print(f"Data will be saved to: {OUTPUT_CSV}")

        with open(OUTPUT_CSV, 'w', encoding='utf-8') as outfile:
            outfile.write("timestamp,x_axis,y_axis,z_axis\n")

            while True:
                try:
                    line = connection.readline().decode('utf-8', errors='ignore').strip()

                    # Expecting 3 comma-separated values per line
                    if line.count(',') == 2:
                        x_val, y_val, z_val = (val.strip() for val in line.split(','))

                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        outfile.write(f"{current_time},{x_val},{y_val},{z_val}\n")
                        outfile.flush()

                        print(f"Recorded -> Time: {current_time} | X: {x_val} | Y: {y_val} | Z: {z_val}")

                except KeyboardInterrupt:
                    print("\nData logging interrupted by user.")
                    break
                except Exception as read_error:
                    print(f"Warning: Could not process line - {read_error}")
                    continue

    except serial.SerialException as serial_err:
        print(f"Failed to open serial port: {serial_err}")
    except Exception as unexpected_err:
        print(f"An error occurred: {unexpected_err}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()
            print("Closed the serial connection.")

if __name__ == "__main__":
    main()
