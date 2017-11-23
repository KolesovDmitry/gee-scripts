#!/usr/bin/env python
# -*- coding: utf-8 -*-


IMAGE_ID = 'LANDSAT/LC8_L1T_TOA_FMASK'

import ee

import pickle
import numpy as np

def cloud_mask(img):
    cloudMask = img.select('fmask').lt(4)
    return img.mask(img.mask().And(cloudMask))


def select_bands(img):
    return img.select("B6", "B5", "B4")


def create_median(geom_mask, begin, end):
    filterParams = ee.ImageCollection(IMAGE_ID).\
        filterBounds(geom_mask).\
        filter(ee.Filter.date(begin, end)).\
        map(cloud_mask).map(select_bands)

    median = filterParams.median()
    clipped_median = median.clip(geom_mask)

    return clipped_median


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

    print(data)

    # get sample
    sample = data.sampleRegions(train_cut, ['Class'], 30);
    print('First 10 feature: ', sample.limit(10));

    seed=2015;
    # ee.Classifier.randomForest(numberOfTrees, variablesPerSplit, minLeafPopulation, bagFraction, outOfBagMode, seed)
    classifier = ee.Classifier.randomForest(500, 3, 100, 0.5, False, seed);

    # Retrain the classifiers using the full dataset.
    RF15 = classifier.train(sample, 'Class');

    # print(RF15.getInfo());
    # Classify the images.
    classified2015 =  data.classify(RF15);
    classified2015b = classified2015.toByte();
    print('classified2015', classified2015b.getInfo());

    # Export

    # TODO: Try to export as numpy array:
    '''
    latlon = classified2015b.reduceRegion(
        reducer=ee.Reducer.toList(),
        geometry=geom_mask,
        scale=30)


    data = np.array((ee.Array(latlon.get("nd")).getInfo()))
    lats = np.array((ee.Array(latlon.get("latitude")).getInfo()))
    lons = np.array((ee.Array(latlon.get("longitude")).getInfo()))

    output = open('data.pkl', 'wb')

    pickle.dump((data, lats, lons), output)
    output.close()
    '''

    # task_config = {
        # 'description': 'imageToDriveExample',
        # 'scale': 30,
        # 'region': geom_mask
    # }
    # Export.image.toDrive(image, description, folder, fileNamePrefix, dimensions, region, scale, crs, crsTransform,
                         # maxPixels, shardSize, fileDimensions, skipEmptyTiles)
    task = ee.batch.Export.image.toDrive(classified2015b, 'exportExample')
    print('Start task')
    task.start()

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
