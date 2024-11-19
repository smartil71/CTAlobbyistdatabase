##################################################################
# header comment! Overview, name, etc.
# Name: Sean Martil
# Class: CS-341 Fall 2024
# Professor Solworth
# Overview: This program is a Chicago Transit Authority (CTA) Database app
#   Users have a list of commands to view and manipulate the CTA daily ridership database
#   Command 1 prints all stations within the database similar to user input
#   Command 2 prints the weekly ridership percentage for a station of choice
#   Command 3 prints the total weekday ridership for each station
#   Command 4 prints all stops of a user selected line color in a direction of choice
#   Command 5 prints the number of stops of each color separated by direction
#   Command 6 prints total yearly ridership for a station of choice, option to plot data
#   Command 7 prints total ridership for a station of a year of choice, option to plot data
#   Command 8 prints total ridership between 2 stations, option to plot data
#   Command 9 prints all stations within a 1 mile radius of latitude/longitude coordinates, option to plot data
##################################################################

import sqlite3
import math
import matplotlib.pyplot as plt

##################################################################  
#
# print_stats
#
# Given a connection to the CTA database, executes various
# SQL queries to retrieve and output basic stats.
#
def print_stats(dbConn):
    dbCursor = dbConn.cursor()
    
    print("General Statistics:")
    #prints total number of stations
    dbCursor.execute("SELECT COUNT(*) FROM Stations;")
    row = dbCursor.fetchone();
    print("  # of stations:", f"{row[0]:,}")
    
    #prints total number of stops
    dbCursor.execute("SELECT COUNT(*) FROM Stops;")
    row = dbCursor.fetchone();
    print("  # of stops:", f"{row[0]:,}")
    
    #prints total number of ride entries
    dbCursor.execute("SELECT COUNT(*) FROM Ridership;")
    row = dbCursor.fetchone();
    print("  # of ride entries:", f"{row[0]:,}")

    #prints date range of ride entries
    dbCursor.execute("SELECT MIN(Date(Ride_Date)), MAX(Date(Ride_Date)) FROM Ridership")
    min_date, max_date = dbCursor.fetchone()
    print(f"  date range: {min_date} - {max_date}")

    #prints total number of Ridership
    dbCursor.execute("SELECT SUM(Num_Riders) FROM Ridership")
    row = dbCursor.fetchone()
    print("  Total ridership:", f"{row[0]:,}")

    print()

#command 1
#Finds all station names that match the user input
def retrieve_stations(dbConn):
    dbCursor = dbConn.cursor()
    print()
    userinput = input("Enter partial station name (wildcards _ and %): ").strip()

    query = """
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE UPPER(Station_Name) LIKE UPPER(?)
        ORDER BY Station_Name ASC
    """

    dbCursor.execute(query, (userinput,))
    results = dbCursor.fetchall()

    if results:
        for row in results:
            print(f"{row[0]} : {row[1]}")
    else:
        print("**No stations found...")

    print()

#command 2
##Given a station name, returns the percentage of riders on weekdays, saturdays, and sundays/holidays
def ridership_percentage(dbConn):
    dbCursor = dbConn.cursor()
    print()
    stationName = input("Enter the name of the station you would like to analyze: ").strip()
    query_Station_ID = """
        SELECT Station_ID
        FROM Stations
        WHERE Station_Name = ?
    """

    dbCursor.execute(query_Station_ID, (stationName,))
    idResult = dbCursor.fetchone()

    if idResult is None:
        print("**No data found...")
        print()
        return
    
    stationID = idResult[0]

    query_calc = """
        SELECT
            SUM(Num_Riders) AS total_riders,
            SUM(CASE WHEN Type_of_Day = 'W' THEN Num_Riders ELSE 0 END) AS weekday_ridership,
            SUM(CASE WHEN Type_of_Day = 'A' THEN Num_Riders ELSE 0 END) AS sat_ridership,
            SUM(CASE WHEN Type_of_Day = 'U' THEN Num_Riders ELSE 0 END) AS sun_ridership
        FROM Ridership
        WHERE Station_ID = ?
    """

    dbCursor.execute(query_calc, (stationID,))
    sums = dbCursor.fetchone()

    if sums is None or sums[0] is None:
        print("**No data found...")
        return
    
    totalRiders, weekdayRidership, satRidership, sunRidership = sums

    if totalRiders > 0:
        weekdayRatio = (weekdayRidership / totalRiders) * 100
        satRatio = (satRidership / totalRiders) * 100
        sunRatio = (sunRidership / totalRiders) * 100
    else:
        weekdayRatio = satRatio = sunRatio = 0

    print(f"Percentage of ridership for the {stationName} station:")
    print(f"  Weekday ridership: {weekdayRidership:,} ({weekdayRatio:.2f}%)")
    print(f"  Saturday ridership: {satRidership:,} ({satRatio:.2f}%)")
    print(f"  Sunday/holiday ridership: {sunRidership:,} ({sunRatio:.2f}%)")
    print(f"  Total ridership: {totalRiders:,}")
    print()

#command 3
#outputs total ridership on weekends, saturdays, and sundays/holidays for each station
def total_ridership(dbConn):
    dbCursor = dbConn.cursor()
    #print()

    weekdayData = []
    satData = []
    sunData = []

    #calculates total ridership for weekends saturdays and sundays/holidays
    query_total_ridership = """
        SELECT
            COALESCE(SUM(CASE WHEN r.Type_of_Day = 'W' THEN r.Num_Riders ELSE 0 END), 0) AS total_weekday_ridership,
            COALESCE(SUM(CASE WHEN r.Type_of_Day = 'A' THEN r.Num_Riders ELSE 0 END), 0) AS total_sat_ridership,
            COALESCE(SUM(CASE WHEN r.Type_of_Day = 'U' THEN r.Num_Riders ELSE 0 END), 0) AS total_sun_ridership
        FROM Ridership r
    """

    dbCursor.execute(query_total_ridership)
    total_ridership = dbCursor.fetchone()

    if total_ridership is None:
        print("**No data found")
        return
    
    #stores query results into respective weekend, saturday, and sunday/holiday variables
    totalWeekdayRiders, totalSatRiders, totalSunRiders = total_ridership

    #calculates total number of riders for WUA for each station
    query_calc = """
    SELECT
        s.Station_ID,
        s.Station_Name,
        COALESCE(SUM(r.Num_Riders), 0) AS total_riders,
        COALESCE(SUM(CASE WHEN r.Type_of_Day = 'W' THEN r.Num_Riders ELSE 0 END), 0) AS weekday_ridership,
        COALESCE(SUM(CASE WHEN r.Type_of_Day = 'A' THEN r.Num_Riders ELSE 0 END), 0) AS sat_ridership,
        COALESCE(SUM(CASE WHEN r.Type_of_Day = 'U' THEN r.Num_Riders ELSE 0 END), 0) AS sun_ridership
    FROM Stations s
    LEFT JOIN Ridership r ON s.Station_ID = r.Station_ID
    GROUP BY s.Station_ID, s.Station_Name
    """

    dbCursor.execute(query_calc)
    sums = dbCursor.fetchall()

    if sums is None:
        print("**No data found...")
        return
    
    for row in sums:
        stationID, stationName, totalRiders, weekdayRiders, satRiders, sunRiders = row
        if totalWeekdayRiders > 0:
            weekdayRatio = (weekdayRiders / totalWeekdayRiders) * 100
        else:
            weekdayRatio = 0;
        if totalSatRiders > 0:
            satRatio = (satRiders / totalSatRiders) * 100
        else:
            satRatio = 0;
        if totalSunRiders > 0:
            sunRatio = (sunRiders / totalSunRiders) * 100
        else:
            sunRatio = 0;

        weekdayData.append((stationName, weekdayRiders, weekdayRatio))
        satData.append((stationName, satRiders, satRatio))
        sunData.append((stationName, sunRiders, sunRatio))

    weekdayData.sort(key=lambda x: x[1], reverse = True)
    satData.sort(key=lambda x: x[1], reverse = True)
    sunData.sort(key=lambda x: x[1], reverse = True)

    print("Ridership on Weekdays for Each Station")
    for stationName, weekdayRiders, weekdayRatio in weekdayData:
        print(f"{stationName} :{totalWeekdayRiders}, {weekdayRiders:,} ({weekdayRatio:.2f}%)")

    print()
    #DEBUGGING, prints ridership for saturdays and sundays/holidays aswell.
    #print("Ridership on Saturdays for Each Station")
    #for stationName, satRiders, satRatio in satData:
    #    print(f"{stationName} : {satRiders:,} ({satRatio:.2f}%)")

    #print()
    #print("Ridership on Sundays/Holidays for Each Station")
    #for stationName, sunRiders, sunRatio in sunData:
    #    print(f"{stationName} : {sunRiders:,} ({sunRatio:.2f}%)")
    #print()

#command 4
#Outputs all stops of line in given direction
def find_line(dbConn):
    dbCursor = dbConn.cursor()
    print()
    lines = {'red', 'blue', 'green', 'brown', 'purple', 'purple-express', 'yellow', 'pink', 'orange'}
    directions = {'n', 's', 'e', 'w', 'north', 'south', 'east', 'west'}

    #asks and checks if line is valid
    lineColor = input("Enter a line color (e.g. Red or Yellow): ").strip().lower()
    if lineColor not in lines:
        print("**No such line...")
        print()
        return
    
    #asks and checks if direction is valid
    direction = input("Enter a direction (N/S/W/E): ").strip().lower()
    if direction not in directions:
        print("**That line does not run in the direction chosen...")
        print()
        return

    dbCursor.execute("SELECT Line_ID FROM Lines WHERE LOWER(Color) = ?", (lineColor,))
    lineIDQuery = dbCursor.fetchone()

    if lineIDQuery is None:
        print("**No such line...")
        print()
        return

    lineID = lineIDQuery[0]

    #Searches for stops of the line id from color and direction
    id_query = """
        SELECT s.Stop_Name, s.Direction, s.ADA
        FROM Stops s
        JOIN StopDetails sd ON s.Stop_ID = sd.Stop_ID
        WHERE sd.Line_ID = ? and LOWER(s.Direction) = ?
        ORDER BY s.Stop_Name ASC
    """

    dbCursor.execute(id_query, (lineID, direction))
    stops = dbCursor.fetchall()

    if not stops:
        print("**That line does not run in the direction chosen...")
        return
    
    for sn, sd, ada in stops:
        if ada == 1:
            ada_status = "handicap accessible"
        else:
            ada_status = "not handicap accessible"
        print(f"{sn} : direction = {sd} ({ada_status})")
    print()

#command 5
#Outputs number of stops for each line by direction, calculates line percentage by total lines
def color_direction(dbConn):
    dbCursor = dbConn.cursor();
    #print()
    print("Number of Stops For Each Color By Direction")

    query = """
        SELECT l.Color, s.Direction, COUNT(*) AS num_stops
        FROM Stops s
        JOIN StopDetails sd ON s.Stop_ID = sd.Stop_ID
        JOIN Lines l ON sd.Line_ID = l.Line_ID
        GROUP BY l.Color, s.Direction
        ORDER BY l.Color ASC, s.Direction ASC
    """

    dbCursor.execute(query)
    query_data = dbCursor.fetchall()

    #sums number of stops for percentage calculations
    query_total_stops = """
        SELECT COUNT(*) AS total_stops
        FROM Stops
    """

    dbCursor.execute(query_total_stops)
    stops_result = dbCursor.fetchone()
    total_stops = stops_result[0]

    if total_stops == 0:
        print("**Error, no stops in the database")
        return
    
    for color, direction, numStops in query_data:
        perc = (numStops / total_stops) * 100
        print(f"{color} going {direction} : {numStops} ({perc:.2f}%)")
    print()

#Command 6
#User enters a station name and total ridership for each year is output to the terminal
#User has option to plot data
def yearly_ridership(dbConn):
    dbCursor = dbConn.cursor()
    print()
    userinput = input("Enter a station name (wildcards _ and %): ").strip()

    dbCursor.execute('''
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE Station_Name LIKE ?
    ''', (userinput,))

    stations = dbCursor.fetchall()

    if len(stations) == 0:
        print("**No station found...")
        print()
        return
    elif len(stations) > 1:
        print("**Multiple stations found...")
        print()
        return

    stid, stname = stations[0]

    dbCursor.execute('''
        SELECT strftime('%Y', Ride_Date) AS Year, SUM(Num_Riders) AS total_riders
        FROM Ridership
        WHERE Station_ID = ?
        GROUP BY Year
        ORDER BY Year ASC
    ''', (stid,))

    ridership_data = dbCursor.fetchall()

    if not ridership_data:
        print("**No station found...")
        print()
        return
    
    #prints data to terminal
    print(f"Yearly Ridership at {stname}")
    for year, total_riders in ridership_data:
        print(f"{year} : {total_riders:,}")
    print()

    #plotting pseudo function
    plotinput = input("Plot? (y/n) ").strip().lower()

    if (plotinput == 'y'):
        years = [int(year) for year, _ in ridership_data]
        total_riders = [total_riders / 1_000_000 for _, total_riders in ridership_data]

        plt.figure(figsize=(12, 8))
        plt.plot(years, total_riders, linestyle='-', color='b')
        plt.xticks(years)
        plt.xlabel('Year')
        plt.ylabel('Number of Riders')
        plt.title(f'Yearly Ridership at {stname} Station')
        plt.grid(False)
        #plt.show()
        plt.savefig('command6.png')
    
    print()

#command 7
#User enters a station name and year and outputs monthly ridership for chosen year
#user has option to plot data
def monthly_ridership(dbConn):
    dbCursor = dbConn.cursor()
    print()
    userinput = input("Enter a station name (wildcards _ and %): ").strip()

    dbCursor.execute('''
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE Station_Name LIKE ?
    ''', (userinput,))

    stations = dbCursor.fetchall()

    if len(stations) == 0:
        print("**No station found...")
        print()
        return
    elif len(stations) > 1:
        print("**Multiple stations found...")
        print()
        return

    targetyear = input("Enter a year: ").strip()
    
    stid, stname = stations[0]

    dbCursor.execute('''
        SELECT strftime('%m', Ride_Date) AS Month, SUM(Num_Riders) as total_riders
        FROM Ridership
        WHERE Station_ID = ? AND strftime('%Y', Ride_Date) = ?
        GROUP BY Month
        ORDER BY Month ASC
    ''', (stid, targetyear))

    ridership_data = dbCursor.fetchall()

    #prints data
    print(f"Monthly Ridership at {stname} for {targetyear}")
    for month, total_riders in ridership_data:
        print(f"{month}/{targetyear} : {total_riders:,}")

    print()

    #plotting pseudo function
    plotinput = input("Plot? (y/n) ").strip().lower()
    if (plotinput == 'y'):
        months = [int(month) for month, _ in ridership_data]
        total_riders = [total_riders for _, total_riders in ridership_data]

        plt.figure(figsize=(12, 8))
        plt.plot(months, total_riders, linestyle='-', color='b')
        plt.xticks(months, [f'{month:02d}' for month in months])
        plt.xlabel('Month')
        plt.ylabel('Number of Riders')
        plt.title(f'Monthy Ridership at {stname} Station {targetyear}')
        plt.grid(False)
        #plt.show()
        plt.savefig('command7.png')
    
    print()

#Helper function of two_station_daily_ridership
#prints ride_date and total_riders as
#YYYY-MM-DD total_riders
def print_ridership(station_name, ridership_data):
    if ridership_data:
        for ride_date, total_riders in ridership_data[:5]:
            print(f"{ride_date} {total_riders}")

        for ride_date, total_riders in ridership_data[-5:]:
            print(f"{ride_date} {total_riders}")

#Helper function of two_station_daily_ridership
#extracts dates and total_riders from ridership_data
def get_ridership_dates(ridership_data):
    dates = [ride_date for ride_date, _ in ridership_data]
    total_riders = [total_riders for _, total_riders in ridership_data]
    return dates, total_riders

#command 8
#Asks user for 2 stations and prints ridership of first 5 and last 5 days of selected year
#user has option to plot data
#this master function essentially just calculates the search queries of both stations
def two_station_daily_ridership(dbConn):
    dbCursor = dbConn.cursor()
    print()
    targetyear = input("Year to compare against? ").strip()
    print()
    station1input = input("Enter station 1 (wildcards _ and %): ").strip()

    dbCursor.execute('''
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE Station_Name LIKE ?
    ''', (station1input,))

    station1_idname = dbCursor.fetchall()

    if len(station1_idname) == 0:
        print("**No station found...")
        print()
        return
    elif len(station1_idname) > 1:
        print("**Multiple stations found...")
        print()
        return
    
    station1id, station1name = station1_idname[0]
    print()
    station2input = input("Enter station 2 (wildcards _ and %): ").strip()

    dbCursor.execute('''
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE Station_Name LIKE ?
    ''', (station2input,))

    station2_idname = dbCursor.fetchall()

    if len(station2_idname) == 0:
        print("**No station found...")
        print()
        return
    elif len(station2_idname) > 1:
        print("**Multiple stations found...")
        print()
        return

    station2id, station2name = station2_idname[0]

    dbCursor.execute('''
        SELECT DATE(Ride_Date), SUM(Num_Riders) AS total_riders
        FROM Ridership
        WHERE Station_ID = ? AND strftime('%Y', Ride_Date) = ?
        GROUP BY Ride_Date
        ORDER BY Ride_Date ASC
    ''', (station1id, targetyear))

    station1_ridership = dbCursor.fetchall()

    dbCursor.execute('''
        SELECT DATE(Ride_Date), SUM(Num_Riders) AS total_riders
        FROM Ridership
        WHERE Station_ID = ? AND strftime('%Y', Ride_Date) = ?
        GROUP BY Ride_Date
        ORDER BY Ride_Date ASC
    ''', (station2id, targetyear))

    station2_ridership = dbCursor.fetchall()

    #print results to terminal
    #calls helper function
    print(f"Station 1: {station1id} {station1name}")
    print_ridership(station1name, station1_ridership)
    print(f"Station 2: {station2id} {station2name}")
    print_ridership(station2name, station2_ridership)

    print()
    
    #plotting pseudo function
    plotinput = input("Plot? (y/n) ").strip().lower()
    if (plotinput == 'y'):
        dates1, ridership1 = get_ridership_dates(station1_ridership)
        dates2, ridership2 = get_ridership_dates(station2_ridership)

        plt.figure(figsize=(14, 7))
        plt.plot(dates1, ridership1, linestyle='-', color='b', label=station1name)
        plt.plot(dates2, ridership2, linestyle='-', color='r', label=station2name)
        plt.xticks([0, 50, 100, 150, 200, 250, 300, 350])
        plt.xlabel('Day')
        plt.ylabel('Number of Riders')
        plt.title(f'Ridership Each Day of {targetyear}')
        plt.legend()
        plt.xticks([0, 50, 100, 150, 200, 250, 300, 350])
        #plt.show()
        plt.savefig('command8.png')
        
    print()

#command 9
#Asks user to input valid latitude and longitude and lists stations within a 1 mile radius of the coordinates
def coordinate(dbConn):
    dbCursor = dbConn.cursor()
    print()
    #ask and validate latitude and longitude
    target_latitude = float(input("Enter a latitude: "))

    if not (40 <= target_latitude <= 43):
        print("**Latitude entered is out of bounds...")
        print()
        return

    target_longitude = float(input("Enter a longitude: "))

    if not (-88 <= target_longitude <= -87):
        print("**Longitude entered is out of bounds...")
        print()
        return

    #print()

    #rough estimates of mile per latitude and longitude 
    latr = round(1/69, 3)
    longr = round(1 / 50, 3)

    #calculate radius boundaries
    min_lat = target_latitude - latr
    max_lat = target_latitude + latr
    min_long = target_longitude - longr
    max_long = target_longitude + longr

    query = """
        SELECT s.Station_Name, st.Latitude, st.Longitude
        FROM Stops st
        JOIN Stations s ON st.Station_ID = s.Station_ID
        WHERE Latitude BETWEEN ? AND ? AND Longitude BETWEEN ? AND ?
        ORDER BY s.Station_Name ASC
    """

    dbCursor.execute(query, (min_lat, max_lat, min_long, max_long))

    nearby_stations_raw = dbCursor.fetchall()
    #check if any stations exist
    if nearby_stations_raw:
        print()

    if not nearby_stations_raw:
        print("**No stations found...")
        print()
        return

    #query returns 2 of each result for some odd reason
    #filters out half so proper number of results
    results = []
    for i in range(0, len(nearby_stations_raw)):
        if i % 2:
            results.append(nearby_stations_raw[i])

    #prints stations
    print("List of Stations Within a Mile")
    for station_name, lat, lon in results:
        print(f"{station_name} : ({lat}, {lon})")
    print()

    #plotting pseudo function
    plotinput = input("Plot? (y/n) ").strip().lower()
    if (plotinput == 'y'):
        lats = [lat for _, lat, _ in results]
        lons = [lon for _, _, lon in results]
        names = [station_name for station_name, _, _ in results]

        image = plt.imread("chicago.png")
        xydims = [-87.9277, -87.5569, 41.7012, 42.0868]
        plt.imshow(image, extent=xydims)
        plt.title("Stations Near You")

        for name, lat, lon in zip(names, lats, lons):
            plt.plot(lat, lon)
            plt.annotate(name, (lat, lon))

        plt.xlim([-87.9277, -87.5569])
        plt.ylim([41.7012, 42.0868])
        #plt.show()
        plt.savefig('command9.png')
    print()

##################################################################  
#
# main
#
print('** Welcome to CTA L analysis app **')
print()

dbConn = sqlite3.connect('CTA2_L_daily_ridership.db')

print_stats(dbConn)

while True:
    command = input("Please enter a command (1-9, x to exit): ").strip()
    #exits program
    if command.lower() == 'x':
        break
    
    if command.isdigit() and (int(command) >= 1 and int(command) <= 9):
        num = int(command)
        if num == 1:
            retrieve_stations(dbConn)
        if num == 2:
            ridership_percentage(dbConn)
        if num == 3:
            total_ridership(dbConn)
        if num == 4:
            find_line(dbConn)
        if num == 5:
            color_direction(dbConn)
        if num == 6:
            yearly_ridership(dbConn)
        if num == 7:
            monthly_ridership(dbConn)
        if num == 8:
            two_station_daily_ridership(dbConn)
        if num == 9:
            coordinate(dbConn)
    else:
        print("**Error, unknown command, try again...")
        print()


#
# done
#
