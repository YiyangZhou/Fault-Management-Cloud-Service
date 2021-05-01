#!/usr/bin/env python
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

secret_id = 'AKIDpPm4GoWuZzBAtNvmpeEdpnVxCuOemYEe'  # 替换为用户的 secretId
secret_key = 'd33pXAbomtzITkqIyFG4cv77tOK2Tfgc'  # 替换为用户的 secretKey

region = 'ap-nanjing'  # 替换为用户的 Region

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)

client = CosS3Client(config)

response = client.create_bucket(
    Bucket='15108293600-1611373650-1304183991',
    ACL="public-read"  #  private  /  public-read / public-read-write
)
