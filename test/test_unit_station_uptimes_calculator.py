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

class Test_Unit_StationUptimesCalculator(unittest.TestCase):
    valid_path = 'test/input_1.txt'
    invalid_path = '12(3'


    # --- parse() tests ---


    def test__parse__charger_uptime_reports_file_path__success(self):
        parsed_arguments = uptimes_calculator.parse([self.valid_path])
        self.assertEqual(parsed_arguments.reports_file_path, self.valid_path)

    def test__parse__invalid_file_path__doesnt_check_so_success(self):
        parsed_args = uptimes_calculator.parse([self.invalid_path])

        self.assertEqual(parsed_args.reports_file_path, self.invalid_path)
    
    @patch('sys.stderr', new_callable=StringIO)
    def test__parse__missing_file_path_argument__system_exit_and_print_arg_info(self, mock_stderr):
        with self.assertRaises(SystemExit):
            uptimes_calculator.parse([])

        err_message_lines = mock_stderr.getvalue().splitlines()
        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn('error: the following arguments are required: reports_file_path', err_message_lines[1])

    @patch('sys.stderr', new_callable=StringIO)
    def test__parse__extra_positional_argument__system_exit_and_print_arg_info(self, mock_stderr):
        extra_argument = '123'

        with self.assertRaises(SystemExit):
            uptimes_calculator.parse([self.valid_path, extra_argument])

        err_message_lines = mock_stderr.getvalue().splitlines()
        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn(f'error: unrecognized arguments: {extra_argument}', err_message_lines[1])

    @patch('sys.stderr', new_callable=StringIO)
    def test__parse__undefined_option_argument__system_exit_and_print_arg_info(self, mock_stderr):
        extra_argument = '--test'

        with self.assertRaises(SystemExit):
            uptimes_calculator.parse([self.valid_path, extra_argument])

        err_message_lines = mock_stderr.getvalue().splitlines()

        self.assertIn('[-h] reports_file_path', err_message_lines[0])
        self.assertIn(f'error: unrecognized arguments: {extra_argument}', err_message_lines[1])


    # --- parse_charger_text_reports() tests ---

    def test__parse_charger_text_reports__realistic_input__success(self):
        with open(self.valid_path, 'r') as file:
            lines = file.readlines()

        chargers_to_stations, charger_reports = uptimes_calculator.parse_charger_text_reports(lines)

        self.assertEqual(chargers_to_stations, {1001: 0, 1002: 0, 1003: 1, 1004: 2})
        self.assertEqual(charger_reports, [uptimes_calculator.ChargerReport(1001, 0, 50000, True), 
                                           uptimes_calculator.ChargerReport(1001, 50000, 100000, True), 
                                           uptimes_calculator.ChargerReport(1002, 50000, 100000, True), 
                                           uptimes_calculator.ChargerReport(1003, 25000, 75000, False), 
                                           uptimes_calculator.ChargerReport(1004, 0, 50000, True), 
                                           uptimes_calculator.ChargerReport(1004, 100000, 200000, True)])

    def test__parse_charger_text_reports__negative_time_stamp__success(self):
        with open('test/data_test_files/input_negative_time.txt', 'r') as file:
            lines = file.readlines()

        chargers_to_stations, charger_reports = uptimes_calculator.parse_charger_text_reports(lines)

        self.assertEqual(chargers_to_stations, {1001: 0})
        self.assertEqual(charger_reports, [uptimes_calculator.ChargerReport(1001, -25000, 50000, True)])

    def test__parse_charger_text_reports__missing_a_station_id_field__cant_check_so_success(self):
        with open('test/data_test_files/input_missing_station_id.txt', 'r') as file:
            lines = file.readlines()

        chargers_to_stations, _ = uptimes_calculator.parse_charger_text_reports(lines)

        self.assertEqual(chargers_to_stations, {1002: 1001, 1003: 1})

    def test__parse_charger_text_reports__missing_stations_section__raise_stations_section_error(self):
        with open('test/data_test_files/input_missing_stations.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.NoStationsSectionError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__missing_charger_availability_reports_section__raise_charger_reports_section_error(self):
        with open('test/data_test_files/input_missing_charger_reports.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.NoChargerReportsSectionError):                
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__missing_stations_and_charger_reports_section__raise_stations_section_error(self):
        with open('test/data_test_files/input_missing_both_sections.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.NoStationsSectionError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__empty_stations_section__raise_empty_stations_section_error(self):
        with open('test/data_test_files/input_empty_stations_section.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.EmptyStationsSectionError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__empty_charger_reports_section__raise_empty_charger_reports_section_error(self):
        with open('test/data_test_files/input_empty_charger_reports_section.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.EmptyChargerReportsSectionError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__empty_list__raise_stations_section_error(self):
        with self.assertRaises(uptimes_calculator.NoStationsSectionError):
            uptimes_calculator.parse_charger_text_reports([])

    def test__parse_charger_text_reports__no_empty_lines_between_sections__raise_invalid_value_error(self):
        with open('test/data_test_files/input_no_empty_lines_between_sections.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__no_new_lines_in_file__raise_stations_section_error(self):
        with open('test/data_test_files/input_no_new_lines.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.NoStationsSectionError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__invalid_station_number_data__raise_invalid_value_error(self):
        with open('test/data_test_files/input_bad_station_data.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__invalid_charger_reports_number_data__raise_invalid_value_error(self):
        with open('test/data_test_files/input_bad_charger_report_data.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__invalid_charger_reports_bool_data__attribute_set_to_false(self):
        with open('test/data_test_files/input_bad_charger_report_bool_data.txt', 'r') as file:
            lines = file.readlines()

        _, charger_reports = uptimes_calculator.parse_charger_text_reports(lines)

        self.assertEqual(charger_reports[0].charger_available, False)

    def test__parse_charger_text_reports__charger_report_missing_station_id__raise_invalid_value_error(self):
        with open('test/data_test_files/input_charger_report_missing_station_id.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
            uptimes_calculator.parse_charger_text_reports(lines)

    def test__parse_charger_text_reports__charger_report_missing_time__raise_invalid_value_error(self):
        with open('test/data_test_files/input_charger_report_missing_time.txt', 'r') as file:
            lines = file.readlines()

        with self.assertRaises(uptimes_calculator.InvalidChargerReportValueError):
            uptimes_calculator.parse_charger_text_reports(lines)


    # --- validate_station_ids_in_reports() tests ---


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


    # --- calculate_station_uptimes() tests ---


    def test__calculate_station_uptimes__realistic_input__correct_uptimes(self):
        chargers_to_stations = {1001: 0, 1002: 0, 1003: 1, 1004: 2}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1001, 50000, 100000, True),
                           uptimes_calculator.ChargerReport(1002, 25000, 100000, True),
                           uptimes_calculator.ChargerReport(1003, 25000, 75000, False),
                           uptimes_calculator.ChargerReport(1004, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1004, 100000, 200000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100), (1, 0), (2, 75)])

    def test__calculate_station_uptimes__timeline_in_negative_range__correct_uptimes(self):
        chargers_to_stations = {1001: 0}
        charger_reports = [uptimes_calculator.ChargerReport(1001, -50000, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])


    # --- --- All variations of the start and end times of the timelines between two concurrent sorted reports --- ---


    def test__calculate_station_uptimes__two_equal_non_existent_report_timelines__only_affect_latest_and_earliest_times(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 0, True),
                           uptimes_calculator.ChargerReport(1002, 0, 0, True),
                           # Prevents timeline error
                           uptimes_calculator.ChargerReport(1001, 50000, 100000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 50)])

    def test__calculate_station_uptimes__second_report_timeline_has_same_start_time_as_first_non_existent_report_timeline__first_report_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 0, True),
                           uptimes_calculator.ChargerReport(1002, 0, 25000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__non_existent_report_timeline_after_another_non_existent_timeline__only_affect_latest_and_earliest_times(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 0, True),
                           uptimes_calculator.ChargerReport(1002, 25000, 25000, True),
                           # Prevents timeline error
                           uptimes_calculator.ChargerReport(1001, 50000, 100000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 50)])

    def test__calculate_station_uptimes__second_report_timeline_after_non_existent_timeline__first_timeline_only_affects_latest_and_earliest_times(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 0, True),
                           uptimes_calculator.ChargerReport(1002, 25000, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 50)])

    def test__calculate_station_uptimes__non_existent_report_timeline_at_start_of_previous_timeline__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 0, 0, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__second_report_timeline_has_same_start_time_as_first_and_ends_inside_first__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 0, 25000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__two_equal_report_timelines__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 0, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__second_report_timeline_has_same_start_as_first_but_ends_past_first__second_timeline_partially_adds_to_uptime(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 25000, True),
                           uptimes_calculator.ChargerReport(1002, 0, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__non_existent_report_timeline_inside_previous_timeline__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 25000, 25000, True),
                           uptimes_calculator.ChargerReport(1002, 0, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__second_report_timeline_inside_previous_timeline__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 75000, True),
                           uptimes_calculator.ChargerReport(1002, 25000, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__second_report_timeline_starts_inside_previous_timeline_and_ends_at_same_time_as_previous__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 25000, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__second_report_timeline_starts_inside_previous_timeline_and_ends_past_previous_timeline__second_timeline_partially_adds_to_uptime(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 25000, 75000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__non_existent_report_timeline_at_end_of_previous_timeline__second_timeline_doesnt_affect_calculations(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 50000, 50000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__second_report_timeline_starts_at_end_of_previous_timeline__second_timeline_fully_adds_to_uptime(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 50000, 75000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 100)])

    def test__calculate_station_uptimes__non_existent_report_timeline_past_end_of_previous_timeline__only_affect_latest_and_earliest_times(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 75000, 75000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 66)])

    def test__calculate_station_uptimes__second_report_timeline_starts_past_end_of_previous_timeline__second_timeline_fully_adds_to_uptime(self):
        chargers_to_stations = {1001: 0, 1002: 0}

        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True),
                           uptimes_calculator.ChargerReport(1002, 75000, 100000, True)]

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 75)])


    # --- --- Bad data --- ---


    def test__calculate_station_uptimes__no_charger_reports__zero_uptime(self):
        chargers_to_stations = {1001: 0, 1002: 0, 1003: 1, 1004: 2}
        charger_reports = []

        uptimes = uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
        self.assertEqual(uptimes, [(0, 0), (1, 0), (2, 0)])

    def test__calculate_station_uptimes__no_stations__key_error(self):
        no_chargers_to_stations = {}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True)]

        with self.assertRaises(KeyError):
            uptimes_calculator.calculate_station_uptimes(no_chargers_to_stations, charger_reports)

    def test__calculate_station_uptimes__no_station_associated_with_reports_charger_id__key_error(self):
        chargers_to_stations = {1003: 3}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 0, 50000, True)]

        with self.assertRaises(KeyError):
            uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)
    
    def test__calculate_station_uptimes__station_timeline_does_not_exist__raise_timeline_error(self):
        chargers_to_stations = {1001: 1}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 50000, 50000, True)]
        
        with self.assertRaises(uptimes_calculator.TimeLineError):
            uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)

    def test__calculate_station_uptimes__inverted_timeline__raise_timeline_error(self):
        chargers_to_stations = {1001: 1}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 50000, -25000, True)]
        
        with self.assertRaises(uptimes_calculator.TimeLineError):
            uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)

    def test__calculate_station_uptimes__infinite_timeline_start__raise_timeline_error(self):
        chargers_to_stations = {1001: 1}
        charger_reports = [uptimes_calculator.ChargerReport(1001, float('-inf'), 1, True)]
        
        with self.assertRaises(uptimes_calculator.TimeLineError):
            uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)

    def test__calculate_station_uptimes__infinite_timeline_end__raise_timeline_error(self):
        chargers_to_stations = {1001: 1}
        charger_reports = [uptimes_calculator.ChargerReport(1001, 1, float('-inf'), True)]
        
        with self.assertRaises(uptimes_calculator.TimeLineError):
            uptimes_calculator.calculate_station_uptimes(chargers_to_stations, charger_reports)


if __name__ == '__main__':
    unittest.main()
