import unittest

from build_editorial_layer import editorial


class EditorialLayerTest(unittest.TestCase):
    def test_discontinued_benefit_is_not_a_strength(self):
        card = {
            "id": "test", "name": "Test card", "annualFeeAmount": 500,
            "rewardLine": "1% cashback", "bestFor": ["cashback"],
            "loungeBenefits": ["Complimentary lounge access was discontinued in April 2026."],
        }
        result = editorial(card, [card])
        self.assertFalse(any("discontinued" in line for line in result["strengths"]))


if __name__ == "__main__":
    unittest.main()
