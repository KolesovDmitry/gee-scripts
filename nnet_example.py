#!/usr/bin/env python
# -*- coding: utf-8 -*-


IMAGE_ID = 'LANDSAT/LC8_L1T_TOA_FMASK'

import ee

from nnet.nnet import Neuron, Layer, NNet


def cloud_mask(img):
    cloudMask = img.select('fmask').lt(4)
    return img.mask(img.mask().And(cloudMask))


def select_bands(img):
    return img.select("B6", "B5", "B4")


def create_median(geom_mask, begin, end):
    ee.Initialize()

    filterParams = ee.ImageCollection(IMAGE_ID).\
        filterBounds(destination).\
        filter(ee.Filter.date(begin, end)).\
        map(cloud_mask).map(select_bands)

    median = filterParams.median()
    clipped_median = median.clip(geom_mask)

    return clipped_median


def main(geom_mask):

    winter1415 = create_median(geom_mask, '2014-11-25', '2015-03-08')
    winter1516 = create_median(geom_mask, '2015-11-25', '2016-03-08')


    # merge together 14 15 var
    data = ee.Image.cat([winter1415, winter1516])
    # Classify the images.

    n1 = Neuron([1, 2, 3, 4, 5, 6], 0)
    n2 = Neuron([1, 1, 1, 1, 1, 1], 0)
    lr1 = Layer([n1, n2])

    n3 = Neuron([1, 1], 1)
    lr2 = Layer([n3])

    nn = NNet([lr1, lr2])

    out = nn.outs(data)
    print(out.getInfo())

    """
    task_config = {
        'scale': 30,
        'region': geom_mask,
        'maxPixels': 50000000000
    }

    # Export.table.toDrive(collection=sample, description='train_sample_ig1', fileFormat='CSV')

    task = ee.batch.Export.image(
        out,
        description='nn_out',
        config=task_config
    )

    print task.status()
    task.start()
    print task.status()
    """


if __name__ == '__main__':
    ee.Initialize()

    # import ipdb; ipdb.set_trace()
    destination = ee.Geometry.Polygon(
        [[136.1212921142578, 46.1646144968971],
         [136.11785888671875, 45.9874205909687],
         [136.60606384277344, 45.98503507715983],
         [136.60400390625, 46.17222297845542],
         [136.1199188232422, 46.17317396465173]])

    main(destination)
