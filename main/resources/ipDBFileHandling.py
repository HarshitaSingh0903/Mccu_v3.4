import csv, socket

ip_file_name=  "ipPortDB.csv"

def validate_ip_address(ip_address):
	try:
		socket.inet_aton(ip_address)
		return True
	except socket.error:
		return False
def create_empty_file():
    with open(ip_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)

def write_ip(ip, port):
    with open(ip_file_name, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([ip])
        csv_writer.writerow([port])

def read_ip_file():
    """ Description of read_ip_file 
    Returns : last line of csv
    """
    with open(ip_file_name, "r") as csvfile:
        lines = csvfile.readlines()
        if lines:
            return lines[-1].strip() 
        else:
            return None

def read_ip_port_from_csv(filename):
    try:
        with open(filename, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            rows = list(csv_reader)
            if len(rows) < 2:
                print("CSV file does not contain both IP and port.")
                return None, None
            ip = rows[0][0]
            port = rows[1][0]
            
            return ip, port
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return None, None

def clear_ip_file(ip_file_name):
    f = open(ip_file_name, "w")
    f.truncate()
    f.close()

def is_csv_empty(ip_file_name):
    """
    Description of is_csv_empty
    Returns:
        not first_char: Returns True if the first_char is an empty string
    """
    with open(ip_file_name, "r") as csvfile:
        first_char = csvfile.read(1)
        return not first_char 