#! /usr/bin/python

import argparse
from dataclasses import dataclass
import math
import sys
from typing import Dict, List

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
class NoStationsSectionError(Exception):
    pass
class EmptyStationsSectionError(Exception):
    pass

class NoChargerReportsSectionError(Exception):
    pass
class EmptyChargerReportsSectionError(Exception):
    pass

class InvalidChargerReportValueError(ValueError):
    """
    Base Error customization based on:
    https://stackoverflow.com/questions/1319615/proper-way-to-declare-custom-exceptions-in-modern-python/26938914#26938914
    """
    def __init__(self, data_field: str, text_line: str, invalid_value: str, *args):
        self.data_field = data_field
        message = f'The data field={data_field} in the text line list at index={text_line} has an invalid value={invalid_value}.'  
        
        # allow users initialize misc. arguments as any other builtin Error
        super(InvalidChargerReportValueError, self).__init__(message, *args)

class TimeLineError(Exception):
    def __init__(self, message: str, *args):
        # allow users initialize misc. arguments as any other builtin Error
        super(TimeLineError, self).__init__(message, *args)

    @classmethod
    def from_non_existent_station_timeline(cls, station_id: int, *args):
        message = f'The timeline of the station that owns charger id={station_id}, does not exist. Its earliest time is equal to its latest.'
        return cls(message, *args)
    
    @classmethod
    def from_charger_report_inverted_timeline(cls, charger_id: int, start_time: int, end_time: int, *args):
        message = f'The timeline of a report with charger id={charger_id}, is inverted: start={start_time}, end={end_time}'
        return cls(message, *args)
    
    @classmethod
    def from_charger_report_infinite_timeline(cls, charger_id: int, start_time: int, end_time: int, *args):
        message = f'The timeline of the report with id={charger_id}, is infinite: start={start_time}, end={end_time}'
        return cls(message, *args)

    parser = argparse.ArgumentParser(description='Calculate station uptimes.')

    reports_path = 'reports_file_path'
    parser.add_argument(reports_path,
                        metavar= reports_path, 
                        type=str,
                        help='Path to charger uptime reports file. <file format requirements here>')

    try:
        parsed_arguments = parser.parse_args(arguments)
    except SystemExit as s:
        print('ERROR')
        raise s

    return parsed_arguments

def parse_charger_text_reports(text_lines: List[str]) -> tuple[Dict[int, int], List[ChargerReport]]:
    
    chargers_to_stations: Dict[int, int] = {}
    charger_reports: List[ChargerReport] = []
    
    try:
        # Find index of the line containing '[Stations]' using generator expression
        station_section_index = next(i for i, line in enumerate(text_lines) if '[Stations]\n' == line)
    except StopIteration:
        raise NoStationsSectionError
    
    line_index = station_section_index + 1
    while line_index < len(text_lines) and not text_lines[line_index].isspace():
        station_entry_list = text_lines[line_index].split()

        try:
            station_id = int(station_entry_list[0])
        except ValueError:
            raise InvalidChargerReportValueError('station_id', line_index, station_entry_list[0])
        
        try:
            station_charger_ids = [int(charger_id) for charger_id in station_entry_list[1:]]
        except ValueError:
            raise InvalidChargerReportValueError('charger_id', line_index, charger_id)
        
        for charger_id in station_charger_ids:
            chargers_to_stations[charger_id] = station_id

        line_index += 1
    
    if chargers_to_stations == {}:
        raise EmptyStationsSectionError

    try:
        charger_section_index = next(i for i, line in enumerate(text_lines) if '[Charger Availability Reports]\n' == line)
    except StopIteration:
        raise NoChargerReportsSectionError
    
    line_index = charger_section_index + 1
    while line_index < len(text_lines) and not text_lines[line_index].isspace():
        charger_entry_list = text_lines[line_index].split()

        try:
            charger_id = int(charger_entry_list[0])
        except ValueError:
            raise InvalidChargerReportValueError('charger_id', line_index, charger_entry_list[0])

        try:
            charger_start_time = int(charger_entry_list[1])
        except ValueError:
            raise InvalidChargerReportValueError('charger_start_time', line_index, charger_entry_list[1])

        try:
            charger_end_time = int(charger_entry_list[2])
        except ValueError:
            raise InvalidChargerReportValueError('charger_end_time', line_index, charger_entry_list[2])

        charger_availability = charger_entry_list[3] == 'true'
        
        charger_reports.append(ChargerReport(charger_id, charger_start_time, charger_end_time, charger_availability))
        line_index += 1

    if charger_reports == []:
        raise EmptyChargerReportsSectionError

    return chargers_to_stations, charger_reports

def validate_station_ids_in_reports(chargers_to_stations: Dict[int, int], charger_reports: List[ChargerReport]) -> tuple[bool, List[int]]:
    """
    Validates that all charger ids in charger_reports exist in chargers_to_stations.

    Returns:
        (bool, List[int]): 
            True if all charger ids in charger_reports exist in chargers_to_stations.

            A list of charger ids that do not exist in chargers_to_stations.
    """

    isValid = True
    missing_station_ids = []

    for report in charger_reports:
        # Using exception handling to run in O(1) time vs 'key in dict' for O(n) time
        try:
            chargers_to_stations[report.charger_id]
        except KeyError:
            isValid = False
            missing_station_ids.append(report.charger_id)

    return isValid, missing_station_ids

def calculate_station_uptimes(chargers_to_stations: Dict[int, int], charger_reports: List[ChargerReport]) -> List[{int, int}]:
    """
    Calculate charger station uptimes based on charger availability reports.

    Raises:
        KeyError: Charger id not found in chargers_to_stations.
        TimeLineError: A report or station's timeline is invalid.
    """
    # TODO: find other exceptions worth documenting
    station_uptime_calculations: Dict[int, StationUptimeCalculationState] = {}
    uptimes = []

    for report in charger_reports:
        if report.start_time > report.end_time:
            raise TimeLineError.from_charger_report_inverted_timeline(report.charger_id, report.start_time, report.end_time)
        if report.start_time == float('-inf') or report.start_time == float('inf') or report.end_time == float('-inf') or report.end_time == float('inf'):
            raise TimeLineError.from_charger_report_infinite_timeline(report.charger_id, report.start_time, report.end_time)

    for station in chargers_to_stations.values():
        station_uptime_calculations[station] = StationUptimeCalculationState(sys.maxsize, 0, float('-inf'), 0)

    sorted_charger_reports = sorted(charger_reports, key=lambda r: r.start_time)

    # Iterate through the sorted list of charger reports and find the earliest start time and latest end time for each station
    for report in sorted_charger_reports:
        station_id = chargers_to_stations[report.charger_id]

        if report.start_time < station_uptime_calculations[station_id].earliest_charger_start_time:
            station_uptime_calculations[station_id].earliest_charger_start_time = report.start_time
        
        if report.end_time > station_uptime_calculations[station_id].latest_charger_end_time:
            station_uptime_calculations[station_id].latest_charger_end_time = report.end_time

    # Validate charger timelines to prevent ZeroDivisionError when calculating uptime percentage
    for id, station_calculation in station_uptime_calculations.items():
        if station_calculation.earliest_charger_start_time == station_calculation.latest_charger_end_time:
            raise TimeLineError.from_non_existent_station_timeline(id)

    # Calculate each station's uptime
    for report in sorted_charger_reports:
        if report.charger_available:
            station_id = chargers_to_stations[report.charger_id]

            if report.start_time >= station_uptime_calculations[station_id].calculation_time:
                station_uptime_calculations[station_id].available_time += report.end_time - report.start_time
                station_uptime_calculations[station_id].calculation_time = report.end_time

            elif report.end_time > station_uptime_calculations[station_id].calculation_time:
                station_uptime_calculations[station_id].available_time += report.end_time - station_uptime_calculations[station_id].calculation_time
                station_uptime_calculations[station_id].calculation_time = report.end_time
    
    # Calculate each station's simplified uptime percentage
    for id, station_calculation in station_uptime_calculations.items():
        uptime_decimal_percentage = station_calculation.available_time / (station_calculation.latest_charger_end_time - station_calculation.earliest_charger_start_time)
        uptime_simplified_percentage = math.trunc(uptime_decimal_percentage * 100)

        uptimes.append((id, uptime_simplified_percentage))

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
        with open(parsed_arguments.reports_file_path, 'r') as file:
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