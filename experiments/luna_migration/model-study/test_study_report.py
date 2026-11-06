"""Offline accounting checks: input partitions and reasoning must not be double billed."""

import copy
import unittest
from decimal import Decimal

from study_report import response_cost


class CostTests(unittest.TestCase):
    def setUp(self):
        self.prices = {"models": {"test": {
            "input": "1", "cached_input": ".05", "cache_write": "1.25", "output": "5",
            "long_context_threshold": 272000,
            "long_input_multiplier": "2", "long_output_multiplier": "1.5",
        }}}
        self.response = {"model": "test", "service_tier": "default", "usage": {
            "prompt_tokens": 10000, "completion_tokens": 1000,
            "prompt_tokens_details": {"cached_tokens": 2000, "cache_write_tokens": 7000},
            "completion_tokens_details": {"reasoning_tokens": 800},
        }}

    def test_partition_and_reasoning_not_added_twice(self):
        cost = response_cost(self.response, self.prices)
        self.assertEqual(cost["uncached_input_tokens"], 1000)
        self.assertEqual(Decimal(cost["total_usd"]), Decimal(".01485"))
        self.assertEqual(Decimal(cost["output_usd"]), Decimal(".005"))

    def test_invalid_or_unreported_usage_fails_explicitly(self):
        bad = copy.deepcopy(self.response)
        bad["usage"]["prompt_tokens_details"]["cache_write_tokens"] = 9000
        with self.assertRaises(ValueError):
            response_cost(bad, self.prices)
        del bad["usage"]["prompt_tokens_details"]["cache_write_tokens"]
        with self.assertRaises(KeyError):
            response_cost(bad, self.prices)

    def test_unpriced_service_tier_is_not_guessed(self):
        self.response["service_tier"] = "priority"
        with self.assertRaises(ValueError):
            response_cost(self.response, self.prices)

    def test_long_context_rate_applies_to_full_request(self):
        self.response["usage"]["prompt_tokens"] = 300000
        cost = response_cost(self.response, self.prices)
        self.assertTrue(cost["long_context"])
        self.assertEqual(Decimal(cost["output_usd"]), Decimal(".0075"))
        self.assertEqual(Decimal(cost["cache_write_usd"]), Decimal(".0175"))


if __name__ == "__main__":
    unittest.main()
