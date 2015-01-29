import luigi
from luigi import configuration
from luigi.contrib.pig import PigJobTask
from luigi.s3 import S3Target, S3PathTask

import inspect
import os
import re

"""
Prerequisites:

    1. Pig installed.
    2. Luigi installed.
    3. The client.cfg file in this directory updated with your s3 and pig settings.

    By default this script will run Pig in local mode.  To run the Pig job on a Hadoop cluster ensure that
    you have Pig configured to connect to your Hadoop cluster and remove the "-x local" options from the
    method pig_options below.

To run:
    python run-olympics-luigi-job.py --local-scheduler --email <Your Email>

"""

class MyPigTask(PigJobTask):
    email = luigi.Parameter(default=None)

    root_path = None

    def pig_script_path(self):
        return 'olympics.pig'

    def pig_env_vars(self):
        return {
                "PIG_CLASSPATH":'%(root)s/.:%(root)s/lib-cluster/*:%(root)s/lib-pig/*' % \
                                        {'root': self._get_root_path()}
        }

    def pig_properties(self):
        return {
            'pig.additional.jars': self._additional_jars(),
            'fs.s3.impl':'org.apache.hadoop.fs.s3native.NativeS3FileSystem',
            'fs.s3n.awsAccessKeyId':self._get_aws_access_key(),
            'fs.s3n.awsSecretAccessKey':self._get_aws_secret_access_key(),
            'fs.s3.awsAccessKeyId':self._get_aws_access_key(),
            'fs.s3.awsSecretAccessKey':self._get_aws_secret_access_key(),
            'pig.exec.reducers.bytes.per.reducer':268435456,
            'fs.default.name':'file:///',
            'pig.temp.dir':'/tmp/',
        }

    def pig_parameters(self):
        #Parameters that Mortar set automatically
        params = {
            'aws_access_key_id':self._get_aws_access_key(),
            'AWS_ACCESS_KEY_ID':self._get_aws_access_key(),
            'AWS_ACCESS_KEY':self._get_aws_access_key(),
            'aws_secret_acces_key':self._get_aws_secret_access_key(),
            'AWS_SECRET_KEY':self._get_aws_secret_access_key(),
            'AWS_SECRET_ACCESS_KEY':self._get_aws_secret_access_key(),
        }
        if self.email:
            params['MORTAR_EMAIL'] = self.email
            params['MORTAR_EMAIL_S3_ESCAPED'] = self._s3_safe(self.email)

        # Set script specific parameters here

        return params

    def pig_options(self):
        options = []

        #Remove this line if you would like to run Pig against a configured cluster
        options += ['-x', 'local']

        return options

    def requires(self):
        return []

    def output(self):
        return [S3Target('s3n://mortar-example-output-data/$MORTAR_EMAIL_S3_ESCAPED/searches_by_age_bucket2')]

    def _additional_jars(self):
        return '%s/lib-cluster/*.jar' % (self._get_root_path())

    def _get_aws_access_key(self):
        return configuration.get_config().get('s3', 'aws_access_key_id')

    def _get_aws_secret_access_key(self):
        return configuration.get_config().get('s3', 'aws_secret_access_key')

    def _get_root_path(self):
        if not self.root_path:
            self.root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        return self.root_path

    def _s3_safe(self, s):
        return re.sub("[^0-9a-zA-Z]", '-', s)

if __name__ == "__main__":
    luigi.run(main_task_cls=MyPigTask)
