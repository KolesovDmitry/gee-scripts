import unittest

from nnet.nnet import Neuron, Layer, NNet

import ee

ee.Initialize()
GEOM_MASK = ee.FeatureCollection([
    ee.Feature(
        ee.Geometry.Polygon(
            [[136.1212921142578, 46.1646144968971],
             [136.11785888671875, 45.9874205909687],
             [136.60606384277344, 45.98503507715983],
             [136.60400390625, 46.17222297845542],
             [136.1199188232422, 46.17317396465173]]),
        {'name': 'mask', 'fill': 1})
])


class TestNeuron(unittest.TestCase):
    def test_out(self):
        inputs = ee.Image([3.0, -1])

        neuron = Neuron([1,2], -1)
        out = neuron.out(inputs)

        output = out.reduceRegion(ee.Reducer.minMax(), GEOM_MASK, scale=30)
        result = output.getInfo()

        result_min = result['constant_min']
        result_max = result['constant_max']

        expected_min = 0.5
        expected_max = 0.5

        self.assertAlmostEqual(expected_max, result_max)
        self.assertAlmostEqual(expected_min, result_min)


class TestLayer(unittest.TestCase):
    def setUp(self):
        neuron1 = Neuron([0.1, 0.2], 0)
        neuron2 = Neuron([0.2, 0.4], 0)
        neuron3 = Neuron([0.3, 0.6], 0)

        self.layer = Layer([neuron1, neuron2, neuron3])

    def test_outs(self):
        inputs = ee.Image([0.3, 0.1])

        out = self.layer.outs(inputs)
        band_list = out.bandNames().getInfo()
        # 3 outputs because of setUp
        self.assertEqual(len(band_list), 3)


        output = out.reduceRegion(ee.Reducer.min(), GEOM_MASK, scale=30)
        result = output.getInfo()

        out1 = result['constant']
        out2 = result['constant_1']
        out3 = result['constant_2']

        # We expect that out3 > out2; out2 > out1 because of setUp function
        self.assertGreater(out3, out2)
        self.assertGreater(out2, out1)


if __name__ == '__main__':
    unittest.main()
