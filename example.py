#!/usr/bin/env python
# -*- coding: utf-8 -*-


IMAGE_ID = 'LANDSAT/LC8_L1T_TOA_FMASK'

from math import exp
import ee


def cloud_mask(img):
    cloudMask = img.select('fmask').lt(4)
    return img.mask(img.mask().And(cloudMask))


def select_bands(img):
    return img.select("B6", "B5", "B4")


def create_median(geom_mask, begin, end):
    filterParams = ee.ImageCollection(IMAGE_ID).\
        filterBounds(destination).\
        filter(ee.Filter.date(begin, end)).\
        map(cloud_mask).map(select_bands)

    median = filterParams.median()
    clipped_median = median.clip(geom_mask)

    return clipped_median


def neuron(inputs, w, bias):
    w = ee.Image(w)
    potential = inputs.multiply(w)
    potential = potential.reduce(ee.Reducer.sum())
    potential = potential.add(ee.Image(bias))

    output = potential.expression(
        '1.0 / (1 + exp(-potential))', {'potential': potential.select('sum')})

    return output


def nnet(input_1, input_2, input_3, input_4, input_5, input_6):
    hidden_pot_1 = -3.44450377987436 + input_1 * (74.3718551556474) + input_2 * (-21.2367519758289) + input_3 * (
        -55.7135867952326) + input_4 * (13.8055979723598) + input_5 * (33.8263553699906) + input_6 * (-4.65603663256619)
    hidden_1 = 1 / (1 + exp(-hidden_pot_1))
    hidden_pot_2 = 1.74165858322656 + input_1 * (-12.9459938873083) + input_2 * (34.9694205850822) + input_3 * (
        -5.16519568791497) + input_4 * (-21.7194850261224) + input_5 * (-17.3280785945837) + input_6 * (71.0147521320201)
    hidden_2 = 1 / (1 + exp(-hidden_pot_2))
    hidden_pot_3 = -0.933320762369686 + input_1 * (-25.6815062078177) + input_2 * (19.0405107028956) + input_3 * (
        30.5258581643624) + input_4 * (-45.6688597695154) + input_5 * (3.50747732974286) + input_6 * (58.4352978956202)
    hidden_3 = 1 / (1 + exp(-hidden_pot_3))
    out_pot1 = 21.4929274624373 + hidden_1 * \
        (45.9907843593617) + hidden_2 * \
        (-29.351969547187) + hidden_3 * (44.488091219665)
    out_neuron_1 = 1 / (1 + exp(-out_pot1))

    return out_neuron_1


def main(geom_mask):
    ee.Initialize()

    mod5_alarms15ig = ee.FeatureCollection(
        'ft:1nSY5gPlvffkZH5-rS02hY5mNw07WwFT7JJ5dYnXn')

    winter1415 = create_median(geom_mask, '2014-11-25', '2015-03-08')
    winter1516 = create_median(geom_mask, '2015-11-25', '2016-03-08')
    # winter1617 = create_median(geom_mask, '2016-11-25', '2017-03-08')

    train_cut = mod5_alarms15ig.filterBounds(geom_mask)

    # merge together 14 15 var
    data = ee.Image.cat([winter1415, winter1516])

    out = neuron(data, range(6), 1)
    print(out.getInfo())


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
