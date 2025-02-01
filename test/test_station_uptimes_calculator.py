from io import StringIO
import sys
import tempfile
from typing import List
import unittest
from unittest.mock import patch
import charger_stats.station_uptimes_calculator as uptimes_calculator

class Test_StationUptimesCalculator(unittest.TestCase):
    valid_path = 'test/input_1.txt'

    def test_parse_charger_uptime_reports_relative_file_path_success(self):
        parsed_arguments = uptimes_calculator.parse([self.valid_path])
        self.assertEqual(parsed_arguments.reports_relative_file_path, self.valid_path)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_parse_missing_file_path_argument_error(self, mock_stdout):
        #with self.assertRaises(SystemExit):
        uptimes_calculator.parse([])
        self.assertEqual(mock_stdout.getvalue(), 'ERROR\n')

    def test_parse_too_many_arguments_error(self):
        with self.assertRaises(SystemExit):
            uptimes_calculator.parse([self.valid_path, '--test'])

    @patch('sys.stderr', new_callable=StringIO)
    def test_parse_charger_text_reports_missing_stations_section_error(self, mock_stderr):
        with open('test/input_missing_stations.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(SystemExit):
            uptimes_calculator.parse_charger_text_reports(lines)

        self.assertEqual(mock_stderr.getvalue(), 'Error: [Stations] section not found in report text.\n')

    def test_parse_charger_text_reports_missing_charger_availability_reports_section_error(self):
        with open('test/input_missing_charger_reports.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(SystemExit):                
            uptimes_calculator.parse_charger_text_reports(lines)

    def test_validate_station_ids_in_reports_valid_and_empty_id_list(self):
        chargers_to_stations = {1001: 0, 1003: 1}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1003, 25000, 75000, False)]

        is_valid, missing_station_ids = uptimes_calculator.validate_station_ids_in_reports(chargers_to_stations, charger_reports)

        self.assertTrue(is_valid)
        self.assertEqual(missing_station_ids, [])

    def test_validate_station_ids_in_reports_with_no_stations_invalid_and_list_missing_ids(self):
        no_chargers_to_stations = {}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1003, 25000, 75000, False)]

        is_valid, missing_station_ids = uptimes_calculator.validate_station_ids_in_reports(no_chargers_to_stations, charger_reports)

        self.assertFalse(is_valid)
        self.assertEqual(missing_station_ids, [1001, 1002])

    '''def test_parse_given_number_instead_of_file_path(self):
        with self.assertRaises(SystemExit):
            uptimes_calculator.parse(['1'])'''

    '''def test_validate_relative_file_path_true(self):
        self.assertTrue(uptimes_calculator.validate('asdf/input_1.txt'))

    def test_validate_invalid_file_path_false(self):
        self.assertFalse(uptimes_calculator.validate('!@#$'))'''

if __name__ == '__main__':
    unittest.main()
