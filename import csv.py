import csv

with open('eurusd.csv', 'r') as file:
    reader = csv.reader(file)
    header = next(reader)

    print("Columns:", header)

    count = 0
    for row in reader:
        print(row)
        count += 1
        if count == 10:
            break
Date,Open,High,Low,Close
2023-06-10,1.0735,1.0751,1.0710,1.0728
2023-06-11,1.0728,1.0760,1.0715,1.0743
2023-06-12,1.0743,1.0785,1.0720,1.0771
2023-06-13,1.0771,1.0790,1.0733,1.0752
2023-06-14,1.0752,1.0800,1.0731,1.0793
