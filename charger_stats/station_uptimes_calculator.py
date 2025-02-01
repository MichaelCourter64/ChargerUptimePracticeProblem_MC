#! /usr/bin/python

import argparse
from dataclasses import dataclass
import math
import sys
import os
import traceback
from typing import Dict, List

# type OneToManyIds = Dict[int, int]

@dataclass
class ChargerReport:
    charger_id: int
    start_time: int
    end_time: int
    charger_available: bool

@dataclass
class StationUptimeCalculationState:
    earliest_charger_start_time: int
    latest_charger_end_time: int
    calculation_time: int
    available_time: int

def parse(arguments: List[str]):
    parser = argparse.ArgumentParser(description='Calculate station uptimes.')

    parser.add_argument('reports_relative_file_path',
                        metavar='Charger uptime reports relative file path.', 
                        type=str,
                        help='Relative path to charger uptime reports file. <file format requirements here>')

    try:
        parsed_arguments = parser.parse_args(arguments)
    except Exception as e:
        print('ERROR')
        raise e

    return parsed_arguments

def parse_charger_text_reports(text_lines: List[str]) -> tuple[Dict[int, int], List[ChargerReport]]:
    
    chargers_to_stations: Dict[int, int] = {}
    charger_reports: List[ChargerReport] = []
    
    try:
        # Find index of the line containing '[Stations]' using generator expression
        station_section_index = next(i for i, line in enumerate(text_lines) if '[Stations]' in line)
    except StopIteration:
        print('ERROR')
        print('Error: [Stations] section not found in report text.', file=sys.stderr)
        sys.exit(1)
    
    line_index = station_section_index + 1
    while line_index < len(text_lines) and not text_lines[line_index].isspace():
        station_entry_list = text_lines[line_index].split()
        station_id = int(station_entry_list[0])
        station_charger_ids = [int(charger_id) for charger_id in station_entry_list[1:]]
        
        for charger_id in station_charger_ids:
            chargers_to_stations[charger_id] = station_id

        line_index += 1
    
    # Find index of the line containing '[Charger Availability Reports]' using generator expression
    try:
        charger_section_index = next(i for i, line in enumerate(text_lines) if '[Charger Availability Reports]' in line)
    except StopIteration:
        print('ERROR')
        print('Error: [Charger Availability Reports] section not found in report text.', file=sys.stderr)
        sys.exit(1)
    
    line_index = charger_section_index + 1
    while line_index < len(text_lines) and not text_lines[line_index].isspace():
        charger_entry_list = text_lines[line_index].split()
        charger_id = int(charger_entry_list[0])
        charger_start_time = int(charger_entry_list[1])
        charger_end_time = int(charger_entry_list[2])
        charger_availability = charger_entry_list[3] == 'true'
        charger_reports.append(ChargerReport(charger_id, charger_start_time, charger_end_time, charger_availability))
        line_index += 1

    return chargers_to_stations, charger_reports

def validate_station_ids_in_reports(chargers_to_stations: Dict[int, int], charger_reports: List[ChargerReport]) -> tuple[bool, List[int]]:
    isValid = True
    missing_station_ids = []

    for report in charger_reports:
        # Use exception handling to run in O(1) time vs 'key in dict' for O(n)
        try:
            chargers_to_stations[report.charger_id]
        except KeyError:
            isValid = False
            missing_station_ids.append(report.charger_id)

    return isValid, missing_station_ids

def calculate_station_uptimes(chargers_to_stations: Dict[int, int], charger_reports: List[ChargerReport]) -> List[{int, int}]:
    uptimes = []

    # Dictionary of station ids to StationUptimeCalculationState
    station_uptime_calculations: Dict[int, StationUptimeCalculationState] = {}
    for station in chargers_to_stations.values():
        station_uptime_calculations[station] = StationUptimeCalculationState(sys.maxsize, 0, 0, 0)

    # Sorted list of charger reports
    sorted_charger_reports = sorted(charger_reports, key=lambda r: r.start_time)

    # Iterate through the sorted list of charger reports and find the earliest start time and latest end time for each station
    for report in sorted_charger_reports:
        station_id = chargers_to_stations[report.charger_id]

        if report.start_time < station_uptime_calculations[station_id].earliest_charger_start_time:
            station_uptime_calculations[station_id].earliest_charger_start_time = report.start_time
        if report.end_time > station_uptime_calculations[station_id].latest_charger_end_time:
            station_uptime_calculations[station_id].latest_charger_end_time = report.end_time

    for report in sorted_charger_reports:
        if report.charger_available:
            station_id = chargers_to_stations[report.charger_id]

            if report.start_time >= station_uptime_calculations[station_id].calculation_time:
                station_uptime_calculations[station_id].available_time += report.end_time - report.start_time
                station_uptime_calculations[station_id].calculation_time = report.end_time
            else:
                station_uptime_calculations[station_id].available_time += report.end_time - station_uptime_calculations[station_id].calculation_time
    
    for id, station_calculation in station_uptime_calculations.items():
        uptimes.append((id, math.trunc(station_calculation.available_time / (station_calculation.latest_charger_end_time - station_calculation.earliest_charger_start_time) * 100)))

    return uptimes

def main():
    cli_arguments = sys.argv[1:]
    parsed_arguments = parse(cli_arguments)

    # Validate the file path
    '''if not validate(parsed_arguments.reports_relative_file_path):
        print('ERROR')
        print(f"Error: The report file path argument '{parsed_arguments.reports_relative_file_path}' is not a valid path.", file=sys.stderr)
        sys.exit(1)'''

    # Read all text from the file
    try:
        with open(os.path.join(os.getcwd(), parsed_arguments.reports_relative_file_path), 'r') as file:
            lines = file.readlines()
    except Exception as e:
        print('ERROR')
        raise e

    chargers_to_stations, charger_reports = parse_charger_text_reports(lines)    

    # Validate station ids in reports
    station_ids_are_valid, missing_station_ids = validate_station_ids_in_reports(chargers_to_stations, charger_reports)
    if not station_ids_are_valid:
        print('ERROR')
        print(f"Error: Station id's '{missing_station_ids}' not found in Station section.", file=sys.stderr)
        sys.exit(1)

    uptimes = calculate_station_uptimes(chargers_to_stations, charger_reports)

    station_sorted_uptimes = sorted(uptimes, key=lambda x: x[0])

    # print the station id and sorted uptimes in the format "<station id> <uptime>"
    for station_id, uptime in station_sorted_uptimes:
        print(f"{station_id} {uptime}")

if __name__ == '__main__':
    main()