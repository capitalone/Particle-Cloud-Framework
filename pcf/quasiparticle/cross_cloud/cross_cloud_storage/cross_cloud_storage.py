# Copyright 2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pcf.core.quasiparticle import Quasiparticle
from pcf.particle.gcp.storage.bucket import Bucket
from pcf.particle.aws.s3.s3_bucket import S3Bucket


class CrossCloudStorage(Quasiparticle):
    """
    This quasiparticle helps manage data across AWS S3 and GCP Storage
    """
    flavor = "cross_cloud_storage"

    def __init__(self, particle_definition):

        particle_definition['particles'] = [{
            "flavor":"s3_bucket",
            "aws_resource":{
                "Bucket": particle_definition.get('storage_name')},
        },{
            "flavor":"storage", 
            "gcp_resource":{
                "name": particle_definition.get('storage_name')}
        }]

        super(CrossCloudStorage, self).__init__(particle_definition)
        s3_particle = self.pcf_field.get_particles(flavor="s3_bucket")
        gcp_particle = self.pcf_field.get_particles(flavor="storage")

        self.s3 = s3_particle['cross_cloud_storage']
        self.storage = gcp_particle['cross_cloud_storage']


    def put_object(self, Bucket, Key, Body=None, Filename=None):
        """
        Puts a file or object in the GCP Storage bucket AWS S3 Bucket
        """
        if Body:
            self.s3.client.put_object(Bucket=Bucket, Key="test-object",Body=Body)
            self.storage.put_object(blob_name="test-object",file_obj=Body)
        elif Filename:
            self.s3.resource.Bucket(Bucket).upload_file(Key="test-file", Filename=Filename)
            self.storage.put_file(blob_name="test-file", file=Filename)


    def delete_object(self, Bucket, Key):
        """
        Delete a file or object in GCP Storage and AWS S3 Bucket
        """
        self.s3.client.delete_object(Bucket=Bucket, Key=Key)
        self.storage.delete_object(blob_name=Key)



