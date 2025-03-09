from io import StringIO
import unittest
from unittest.mock import patch

import charger_stats.station_uptimes_calculator as uptimes_calculator

# Test names use snake case with double underscores separating concepts in 
# the following format: test__<function>__<scenario>__<expected result>
#
# The importance of prepended/appended double underscores in Python was a 
# consideration when choosing the above format.
#
# If use of real text files for testing is an issue in the future, consider 
# using patch()'s side_effect parameter with mock open().

class Test_Integration_StationUptimesCalculator(unittest.TestCase):
    universal_stdout_error_message = 'ERROR\n'
    valid_path = 'test/input_1.txt'
    invalid_path = '12(3'
    missing_stations_error_message = 'Error: [Stations] section not found in report text.\n'


    # --- Argument tests ---


    @patch('sys.stdout', new_callable=StringIO)
    def test__main__invalid_file_path___file_not_found_and_print_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', self.invalid_path]):
            with self.assertRaises(FileNotFoundError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), self.universal_stdout_error_message)
    
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test__main__missing_file_path_argument__system_exit_and_print_error_and_arg_info(self, mock_stdout, mock_stderr):

        with patch('sys.argv', ['station_uptimes_calculator.py']):
            with self.assertRaises(SystemExit):
                uptimes_calculator.main()

        self.assertEqual(mock_stdout.getvalue(), self.universal_stdout_error_message)

        err_message_lines = mock_stderr.getvalue().splitlines()
        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn('error: the following arguments are required: reports_file_path', err_message_lines[1])

    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test__main__extra_positional_argument__system_exit_and_print_error_and_arg_info(self, mock_stdout, mock_stderr):

        extra_argument = '123'
        with patch('sys.argv', ['station_uptimes_calculator.py', self.valid_path, extra_argument]):
            with self.assertRaises(SystemExit):
                uptimes_calculator.main()

        self.assertEqual(mock_stdout.getvalue(), self.universal_stdout_error_message)

        err_message_lines = mock_stderr.getvalue().splitlines()
        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn(f'error: unrecognized arguments: {extra_argument}', err_message_lines[1])

    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test__main__undefined_option_argument__system_exit_and_print_error_and_arg_info(self, mock_stdout, mock_stderr):

        extra_argument = '--test'
        with patch('sys.argv', ['station_uptimes_calculator.py', self.valid_path, extra_argument]):
            with self.assertRaises(SystemExit):
                uptimes_calculator.main()

        self.assertEqual(mock_stdout.getvalue(), self.universal_stdout_error_message)

        err_message_lines = mock_stderr.getvalue().splitlines()
        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn(f'error: unrecognized arguments: {extra_argument}', err_message_lines[1])


    # --- Data tests ---
    

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__realistic_input__correct_uptimes(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', self.valid_path]):
            uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), '0 100\n1 0\n2 75\n')

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__missing_stations_section__raise_stations_section_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_missing_stations.txt']):
            with self.assertRaises(uptimes_calculator.NoStationsSectionError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__missing_charger_availability_reports_section__raise_charger_reports_section_error(self, mock_stdout):
        
        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_missing_charger_reports.txt']):
            with self.assertRaises(uptimes_calculator.NoChargerReportsSectionError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__missing_stations_and_charger_reports_section__raise_stations_section_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_missing_both_sections.txt']):
            with self.assertRaises(uptimes_calculator.NoStationsSectionError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__empty_stations_section__raise_empty_stations_section_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_empty_stations_section.txt']):
            with self.assertRaises(uptimes_calculator.EmptyStationsSectionError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__empty_charger_reports_section__raise_empty_charger_reports_section_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_empty_charger_reports_section.txt']):
            with self.assertRaises(uptimes_calculator.EmptyChargerReportsSectionError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__empty_list__raise_stations_section_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_empty_file.txt']):
            with self.assertRaises(uptimes_calculator.NoStationsSectionError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__no_empty_lines_between_sections__raise_invalid_value_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_no_empty_lines_between_sections.txt']):
            with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__invalid_station_number_data__raise_invalid_value_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_bad_station_data.txt']):
            with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__invalid_charger_reports_number_data__raise_invalid_value_error(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_bad_charger_report_data.txt']):
            with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
                uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), "ERROR\n")

    @patch('sys.stdout', new_callable=StringIO)
    def test__main__invalid_charger_reports_bool_data__attribute_set_to_false(self, mock_stdout):

        with patch('sys.argv', ['station_uptimes_calculator.py', 'test/data_test_files/input_bad_charger_report_bool_data.txt']):
            uptimes_calculator.main()
        self.assertEqual(mock_stdout.getvalue(), '0 50\n1 0\n2 75\n')
