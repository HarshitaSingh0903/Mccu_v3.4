import os
import csv

csv_file = 'satelliteDb.csv'
csv_file2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sat3.csv")

# with open(csv_file, mode='r', newline='') as file:
#     reader = csv.reader(file)
#     data = list(reader)
# Example data with three rows and four columns

def write_csv_without_header(filename):
#     # Open the CSV file for writing
#     data = [
#     ['GSAT-15,11697.50,0,25,90,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957"']
#     ['GSAT-9,11698.50,0,-69,95,"1 42695U 17024A   23176.72381472 -.00000272  00000+0  00000+0 0  9993,2 42695   0.0600  98.2318 0001797 329.7089 203.5151  1.00274819 22527"']
#     [GSAT-10,11698.50,0,-69,95,"1 42695U 17024A   23176.72381472 -.00000272  00000+0  00000+0 0  9993,2 42695   0.0600  98.2318 0001797 329.7089 203.5151  1.00274819 22527'],
# ],
#     ]
    data= [("GSAT-15",0,0,93.5,0,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957"),
           ("GSAT-10",0,0,83.05,0,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957"),
           ("GSAT-7",0,0,74.05,0,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957"),
           ("SES-8",0,0,95,0,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957"),
           ("SES-7",0,0,108.2,0,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957")]
    # with open(csv_file, mode='w', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(row_data)
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row)


def delRow(rowToDelete):
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        data = list(reader)
        if 0 <=rowToDelete < len(data):
            data.pop(rowToDelete)
            with open(csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
            # print(f"Row {rowToDelete} removed successfully.")
        else:
            print(f"Row {rowToDelete} does not exist in the CSV file.")

def add_row_to_csv(row_data):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row_data)

def edit_row_in_csv(row_index, new_data):
    """
    Edit a row in a CSV file.

    :param csv_file: Path to the CSV file.
    :param row_index: Index of the row to edit (0-based index).
    :param new_data: List of new values for each column in the row.
    """
    # Read the CSV file into a list of lists
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        data = list(reader)

    # Check if the row index to edit is valid
    if 0 <= row_index < len(data):
        # Update the row with new data
        data[row_index] = new_data

        # Write the updated data back to the CSV file
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        # print(f"Row {row_index} edited successfully.")
    else:
        print(f"Row {row_index} does not exist in the CSV file.")


new_data = ["NewValue1", "NewValue2", "NewValue3", "NewValue4"]  # Replace with the new data
# edit_row_in_csv(csv_file, 2, new_data)