from io import StringIO
import unittest
from unittest.mock import patch
import charger_stats.station_uptimes_calculator as uptimes_calculator

# Test names use snake case with double underscores separating concepts in 
# the following format: test__<function>__<scenario>__<expected result>
#
# The importance of prepended/appended double underscores in Python was a 
# consideration when choosing the above format.

class Test_StationUptimesCalculator(unittest.TestCase):
    universal_std_error_message = 'ERROR\n'
    valid_path = 'test/input_1.txt'


    def test__parse__charger_uptime_reports_file_path__success(self):
        parsed_arguments = uptimes_calculator.parse([self.valid_path])
        self.assertEqual(parsed_arguments.reports_file_path, self.valid_path)
    
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test__parse__missing_file_path_argument__log_and_exit(self, mock_stdout, mock_stderr):
        with self.assertRaises(SystemExit):
            uptimes_calculator.parse([])

        out_message = mock_stdout.getvalue()
        err_message_lines = mock_stderr.getvalue().splitlines()

        self.assertEqual(out_message, self.universal_std_error_message)
        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn('error: the following arguments are required: reports_file_path', err_message_lines[1])

    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test__parse__too_many_arguments__log_and_exit(self, mock_stdout, mock_stderr):
        with self.assertRaises(SystemExit):
            uptimes_calculator.parse([self.valid_path, '--test'])

        self.assertEqual(mock_stdout.getvalue(), self.universal_std_error_message)

    @patch('sys.stderr', new_callable=StringIO)
    def test__parse_charger_text_reports__missing_stations_section__error(self, mock_stderr):
        with open('test/input_missing_stations.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(SystemExit):
            uptimes_calculator.parse_charger_text_reports(lines)

        self.assertEqual(mock_stderr.getvalue(), 'Error: [Stations] section not found in report text.\n')

    def test__parse_charger_text_reports__missing_charger_availability_reports_section__error(self):
        with open('test/input_missing_charger_reports.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(SystemExit):                
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__validate_station_ids_in_reports__correct_input__valid_and_empty_id_list(self):
        chargers_to_stations = {1001: 0, 1003: 1}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1003, 25000, 75000, False)]

        is_valid, missing_station_ids = uptimes_calculator.validate_station_ids_in_reports(chargers_to_stations, charger_reports)

        self.assertTrue(is_valid)
        self.assertEqual(missing_station_ids, [])

    def test__validate_station_ids_in_reports__no_stations__invalid_and_list_missing_ids(self):
        no_chargers_to_stations = {}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1003, 25000, 75000, False)]

        is_valid, missing_station_ids = uptimes_calculator.validate_station_ids_in_reports(no_chargers_to_stations, charger_reports)

        self.assertFalse(is_valid)
        self.assertEqual(missing_station_ids, [1001, 1003])

    def test__validate_station_ids_in_reports__no_charger_reports__valid_and_no_missing_ids(self):
        chargers_to_stations = {0: [1001, 1002], 1: [1003]}
        missing_charger_reports = []

        is_valid, missing_station_ids = uptimes_calculator.validate_station_ids_in_reports(chargers_to_stations, missing_charger_reports)
        self.assertTrue(is_valid)
        self.assertEqual(missing_station_ids, [])

    '''def test_parse_given_number_instead_of_file_path(self):
        with self.assertRaises(SystemExit):
            uptimes_calculator.parse(['1'])'''

    '''def test_validate_relative_file_path_true(self):
        self.assertTrue(uptimes_calculator.validate('asdf/input_1.txt'))

    def test_validate_invalid_file_path_false(self):
        self.assertFalse(uptimes_calculator.validate('!@#$'))'''

if __name__ == '__main__':
    unittest.main()
