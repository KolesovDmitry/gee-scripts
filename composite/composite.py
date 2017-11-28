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
        self.collection = ee.ImageCollection(self.collection_name)


    @property
    def _l7(self):
        """Return True if the collection is LANDSAT-7"""
        return self.collection_name[:12] == 'LANDSAT/LC07'

    @property
    def _l8(self):
        """Return True if the collection is LANDSAT-8"""
        return self.collection_name[:12] == 'LANDSAT/LC08'

    def aggregator(self, collection):
        if self.function_name == 'median':
            return collection.median()


    def createMedians(self, geom_mask, year,beginDay, endDay, period):
        imgList = []
        begin = beginDay
        while (begin < endDay):
            filters = combine_filter(geom_mask, year, beginDay, beginDay+period)

            filterParams = self.collection.filter(filters)
            filterParams.filterMetadata('CLOUD_COVER','less_than', 50).map(filterCloudL7).map(selectBandsL7)

            collection = ee.ImageCollection(filterParams)

            median = self.aggregator(collection)
            comp16d = median.set('id', 'L78_16d_'+ str(year)+'_'+str(begin + period))
            clippedMedian = comp16d.clip(geom_mask)
            imgList.append(clippedMedian)
            begin += period

        return ee.ImageCollection(imgList)




if __name__ == '__main__':
    # Example of using:
    ee.Initialize()

    destination = ee.Geometry.Polygon(
        [[136.1212921142578, 46.1646144968971],
         [136.11785888671875, 45.9874205909687],
         [136.60606384277344, 45.98503507715983],
         [136.60400390625, 46.17222297845542],
         [136.1199188232422, 46.17317396465173]])

    aggregator = Aggregator('LANDSAT/LE07/C01/T1_RT_TOA')
    tmp = aggregator.createMedians(destination, 2017, 100, 160, 10)
    tmp = tmp.getInfo()
    print tmp
