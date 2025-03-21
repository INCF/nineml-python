from __future__ import print_function
from builtins import zip
from collections import OrderedDict
import unittest
from nineml.values import RandomDistributionValue
from nineml.user.randomdistribution import RandomDistributionProperties
from nineml.abstraction.randomdistribution.base import RandomDistribution
from nineml.abstraction.base import Parameter


class TestRandomDistributionValue(unittest.TestCase):
    """Test the RandomDistributionValue class, particularly the key method."""

    def test_key_includes_properties_hash(self):
        """Test that the key method includes a hash of the properties."""
        # Create two distributions with same name but different properties
        normal_dist = RandomDistribution(
            name='normal',
            standard_library='http://www.uncertml.org/distributions/normal',
            parameters=[
                Parameter('mean'),
                Parameter('variance')
            ])

        dist1 = RandomDistributionProperties(
            name='normal',
            definition=normal_dist,
            properties={'mean': 0.0, 'variance': 1.0})
        
        dist2 = RandomDistributionProperties(
            name='normal',
            definition=normal_dist,
            properties={'mean': 1.0, 'variance': 2.0})

        # Create RandomDistributionValues
        val1 = RandomDistributionValue(dist1)
        val2 = RandomDistributionValue(dist2)

        # Test that keys are different for different properties
        self.assertNotEqual(val1.key, val2.key)

        # Test that keys are same for same properties
        val3 = RandomDistributionValue(dist1)
        self.assertEqual(val1.key, val3.key)

        # Test that key contains distribution name
        self.assertTrue(val1.key.startswith('normal_'))
        self.assertTrue(val2.key.startswith('normal_'))

        # Test that key contains hash
        self.assertTrue('_' in val1.key)
        self.assertTrue('_' in val2.key)


if __name__ == '__main__':
    unittest.main()
