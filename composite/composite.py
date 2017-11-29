import ee


def filterCloudL8(img):
    cloudMask = img.select('BQA').lt(28000)
    return img.mask(img.mask().And(cloudMask))


def filterCloudL7(img):
    cloud = ee.Algorithms.Landsat.simpleCloudScore(img)
    score = cloud.select(['cloud']).lte(30)
    return img.updateMask(score)


def selectBandsL8(img):
  # select only 3 bands
  return img.expression('b("B7","B6","B5","B4","B3","B2")*10000').rename('swir2','swir1','nir','red','green','blue').uint16()

def selectBandsL7(img):
  # select only 3 bands
  return img.expression('b("B7","B5","B4","B3","B2","B1")*10000').rename('swir2','swir1','nir','red','green','blue').uint16()


def data_filter(year, begin_day, end_day):
    flt = ee.Filter([
        ee.Filter.calendarRange(year, year, 'year'),
        ee.Filter.dayOfYear(begin_day, end_day)
    ])
    return flt


def combine_filter(geom, year, begin_day, end_day):
    f = ee.Filter([
        data_filter(year, begin_day, end_day),
        ee.Filter.geometry(geom)
    ])
    return f


class Aggregator:
    def __init__(self, collection_name, function='median'):
        self.function_name = function
        if self.function_name != 'median':
            raise NotImplementedError('Aggregate function %s is not implemented yet' % (self.function_name))

        self.collection_name = collection_name
        if not (self._l7 or self._l8):
            raise NotImplementedError('Aggregation for ImageCollection %s is not implemented yet' % (self.collection_name))
        self.collection = ee.ImageCollection(self.collection_name)


    @property
    def _l7(self):
        """Return True if the collection is LANDSAT-7"""
        return self.collection_name[:12] == 'LANDSAT/LE07'

    @property
    def _l8(self):
        """Return True if the collection is LANDSAT-8"""
        return self.collection_name[:12] == 'LANDSAT/LC08'

    def _aggregator(self, collection):
        if self.function_name == 'median':
            return collection.median()

    def filter_cloud(self, collection, cloud_perc=50):
        """Filter clouds using metadata and BQA|Algoritms.Landsat"""
        collection.filterMetadata('CLOUD_COVER','less_than', cloud_perc)

        if self._l7:
            collection = collection.map(filterCloudL7)
        elif self._l8:
            collection = collection.map(filterCloudL8)
        else:
            raise NotImplementedError('This type of ImageCollection is not implemented')

        return collection

    def select_bands(self, collection):
        """Filter clouds using metadata and BQA|Algoritms.Landsat"""
        if self._l7:
            collection = collection.map(selectBandsL7)
        elif self._l8:
            collection = collection.map(selectBandsL8)
        else:
            raise NotImplementedError('This type of ImageCollection is not implemented')

        return collection

    def aggregate(self, geom_mask, year,beginDay, endDay, period):
        """Apply aggregation function, return ee.ImageCollection"""

        imgList = []
        begin = beginDay
        while (begin < endDay):
            filters = combine_filter(geom_mask, year, beginDay, beginDay+period)

            filtered_collection = self.collection.filter(filters)
            filtered_collection = self.filter_cloud(filtered_collection)
            filtered_collection = self.select_bands(filtered_collection)

            agg_collection = self._aggregator(filtered_collection)
            comp = agg_collection.set('id', "L_%s_%s_%s" % (year, begin, period))
            clipped = comp.clip(geom_mask)
            imgList.append(clipped)
            begin += period

        return ee.ImageCollection(imgList)




if __name__ == '__main__':
    # Example of using:
    ee.Initialize()

    destination = ee.Geometry.Polygon(
        [[49.03250,55.79693],
         [49.118039,55.835827],
         [49.216189,55.804547],
         [49.169160,55.767073]])

    aggregator = Aggregator('LANDSAT/LE07/C01/T1_RT_TOA')
    tmp = aggregator.aggregate(destination, 2017, 100, 260, 10)

    # task = ee.batch.Export.image.toDrive(tmp, 'LandsatComposite')
    # print('Start task')
    # task.start()

    tmp = tmp.getInfo()
    print tmp
