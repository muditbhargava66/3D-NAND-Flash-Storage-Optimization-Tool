# src/firmware_integration/test_benches.py

import unittest
from utils.nand_simulator import NANDSimulator

class TestBenchRunner:
    def __init__(self, test_cases_file):
        with open(test_cases_file, 'r') as file:
            self.test_cases = yaml.safe_load(file)

    def run_tests(self):
        test_suite = unittest.TestSuite()
        for test_case in self.test_cases:
            test_class = type(test_case['name'], (unittest.TestCase,), {})
            test_class.simulator = NANDSimulator(test_case['nand_config'])

            for test_method in test_case['test_methods']:
                test_func = self._create_test_method(test_method)
                setattr(test_class, test_method['name'], test_func)

            test_suite.addTest(unittest.makeSuite(test_class))

        test_runner = unittest.TextTestRunner(verbosity=2)
        test_runner.run(test_suite)

    def _create_test_method(self, test_method):
        def test_func(self):
            self.simulator.execute_sequence(test_method['sequence'])
            expected_output = test_method['expected_output']
            actual_output = self.simulator.get_output()
            self.assertEqual(actual_output, expected_output)
        return test_func