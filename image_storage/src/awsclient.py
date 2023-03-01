import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta


class AwsClient:
    def __init__(self):
        self.s3 = boto3.resource('s3')
        self.s3cli = boto3.client('s3')
        self.cw = boto3.client('cloudwatch')
        self.rds = boto3.client('rds')
        # the bucket is created on aws previous to using the code
        self.bk = "ece1779customimages"

    def s3_clear(self):
        s3_bucket = self.s3.Bucket(self.bk)
        s3_bucket.objects.all().delete()
        return

    def s3_items(self):
        items = []
        s3_bucket = self.s3.Bucket(self.bk)
        for my_bucket_object in s3_bucket.objects.all():
            items.append(my_bucket_object.key)
        return items

    def s3_write(self, file, filename):
        self.s3cli.put_object(Body=file,
                              Bucket=self.bk,
                              Key=filename)
        return

    def s3_read(self, file_name):
        """input filename , read from s3 and return file in bytes"""
        try:
            self.s3.Object(self.bk, file_name).load()
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                # The key does not exist.
                return
            elif e.response['Error']['Code'] == 403:
                # Unauthorized, including invalid bucket
                return
            else:
                # Something else has gone wrong.
                raise
        else:
            obj = self.s3.Object(self.bk, file_name)
            return obj.get()['Body'].read()

    def cw_put(self, miss_rate, hit_rate, num_items, size_of_items, num_requests):
        """put metrics to cloudwatch"""
        response = self.cw.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'miss_rate',
                    'Unit': 'None',
                    'Value': miss_rate,
                    'StorageResolution': 1,
                },
                {
                    'MetricName': 'hit_rate',
                    'Unit': 'None',
                    'Value': hit_rate,
                    'StorageResolution': 1,
                },
                {
                    'MetricName': 'number_of_items_in_cache',
                    'Unit': 'None',
                    'Value': num_items,
                    'StorageResolution': 1,
                },
                {
                    'MetricName': 'total_size_of_items_in_cache',
                    'Unit': 'None',
                    'Value': size_of_items,
                    'StorageResolution': 1,
                },
                {
                    'MetricName': 'number_of_request_per_second',
                    'Unit': 'None',
                    'Value': num_requests,
                    'StorageResolution': 1,
                },
            ],
            Namespace="Cache_pool_statistics"
        )
        return response

    def cw_get(self, metric):
        """ get cloudwatch datapoints for last 30 minutes at 1-minute granularity, Legal input includes 'miss_rate',
        'hit_rate','number_of_items_in_cache', 'total_size_of_items_in_cache','number_of_request_per_second' """
        response = self.cw.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'string',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': "Cache_pool_statistics",
                            'MetricName': metric,
                        },
                        'Period': 60,  # at 1-minute granularity
                        'Stat': 'Average',
                        'Unit': 'None'
                    },
                },
            ],
            StartTime=datetime.utcnow() - timedelta(seconds=1800),  # data for last 30 mins
            EndTime=datetime.utcnow(),
            ScanBy='TimestampAscending',
        )
        return response['MetricDataResults'][0]['Values']

    # def cw_stat(self,metric):
    #     """ get statistics Legal input includes 'miss_rate','hit_rate','number_of_items_in_cache',
    #     'total_size_of_items_in_cache','number_of_request_per_second' """
    #     response = self.cw.get_metric_statistics(
    #         Namespace="Cache_pool_statistics",
    #         MetricName=metric,
    #         Dimensions=[],
    #         StartTime=datetime.utcnow() - timedelta(seconds = 60),
    #         EndTime=datetime.utcnow(),
    #         Period=1,
    #         Statistics=[
    #             'SampleCount'
    #         ],
    #         Unit='None'
    #     )
    #
    #     return response["Datapoints"]
