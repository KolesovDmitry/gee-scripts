import ee


def is_l7(collection_name):
    """Return True if the collection is LANDSAT-7"""
    return collection_name[:12] == 'LANDSAT/LE07'


def is_l8(collection_name):
    """Return True if the collection is LANDSAT-8"""
    return collection_name[:12] == 'LANDSAT/LC08'


def filterCloudL8(img):
    cloudMask = img.select('BQA').lt(28000)
    return img.mask(img.mask().And(cloudMask))


def filterCloudL7(img):
    cloud = ee.Algorithms.Landsat.simpleCloudScore(img)
    score = cloud.select(['cloud']).lte(30)
    return img.updateMask(score)

#TODO: allow to seclect bands in runtime
def selectBandsL8(img):
  return img.expression('b("B6","B5","B4","B3","B2")').rename('swir1','nir','red','green','blue')

#TODO: allow to seclect bands in runtime
def selectBandsL7(img):
  return img.expression('b("B5","B4","B3","B2","B1")').rename('swir1','nir','red','green','blue')


def combine_filter(geom, year, begin_day, end_day):
    f = ee.Filter([
        ee.Filter.calendarRange(year, year, 'year'),
        ee.Filter.dayOfYear(begin_day, end_day),
        ee.Filter.geometry(geom)
    ])
    return f


class Aggregator:
    def __init__(self, collection_list, function='median'):
        self.function_name = function
        if self.function_name not in ['median', 'count', 'min', 'max', 'mode', 'mean', 'product', 'sum']:
            raise NotImplementedError('Aggregate function %s is not implemented yet' % (self.function_name))

        self.collection_list = collection_list
        for collection in self.collection_list:
            if not (is_l7(collection) or is_l8(collection)):
                raise NotImplementedError('Aggregation for ImageCollection %s is not implemented yet' % (self.collection_name))


    def _aggregator(self, collection):
        if self.function_name == 'median':
            return collection.median()
        if self.function_name == 'count':
            return collection.count()

        if self.function_name == 'max':
            return collection.max()
        if self.function_name == 'min':
            return collection.min()

        if self.function_name == 'mode':
            return collection.mode()
        if self.function_name == 'mean':
            return collection.mean()

        if self.function_name == 'product':
            return collection.product()
        if self.function_name == 'sum':
            return collection.sum()




    def filter_cloud(self, collection_id, collection, cloud_perc=50):
        """Filter clouds using metadata and BQA|Algoritms.Landsat"""
        collection.filterMetadata('CLOUD_COVER','less_than', cloud_perc)

        if is_l7(collection_id):
            collection = collection.map(filterCloudL7)
        elif is_l8(collection_id):
            collection = collection.map(filterCloudL8)
        else:
            raise NotImplementedError('This type of ImageCollection is not implemented')

        return collection

    def select_bands(self, collection_id, collection):
        if is_l7(collection_id):
            collection = collection.map(selectBandsL7)
        elif is_l8(collection_id):
            collection = collection.map(selectBandsL8)
        else:
            raise NotImplementedError('This type of ImageCollection is not implemented')

        return collection

    def aggregate(self, geom_mask, year,beginDay, endDay, period):
        """Apply aggregation function, return ee.ImageCollection"""
        imgList = []
        begin = beginDay
        while (begin < endDay):
            filters = combine_filter(geom_mask, year, begin, begin+period)

            # Merge all coolections into one
            merged_collection = None
            for i, collection_id in enumerate(self.collection_list):
                filtered_collection = ee.ImageCollection(collection_id).filter(filters)
                filtered_collection = self.filter_cloud(collection_id, filtered_collection)
                filtered_collection = self.select_bands(collection_id, filtered_collection)

                if i == 0:  # first iteration?
                    merged_collection = filtered_collection
                else:
                    merged_collection.merge(filtered_collection)

            collection = ee.ImageCollection(merged_collection)

            agg_collection = self._aggregator(collection)
            clipped = agg_collection.clip(geom_mask).set('id', "L_%s_%s_%s" % (year, begin, period))
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

    aggregator = Aggregator(['LANDSAT/LE07/C01/T1_RT_TOA' , 'LANDSAT/LC08/C01/T1_RT_TOA'])
    tmp = aggregator.aggregate(destination, 2017, 100, 260, 10)

    # task = ee.batch.Export.image.toDrive(tmp, 'LandsatComposite')
    # print('Start task')
    # task.start()

    # task = ee.batch.Export.image.toAsset(image=tmp.first(), assetId='users/kolesovdm/test', scale=30)
    # print('Start task')
    # task.start()

    tmp = tmp.getInfo()
    # import ipdb;ipdb.set_trace()
    print tmp
