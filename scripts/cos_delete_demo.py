# appid 已在配置中移除,请在参数 Bucket 中带上 appid。Bucket 由 BucketName-APPID 组成
# 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client


secret_id = 'AKIDpPm4GoWuZzBAtNvmpeEdpnVxCuOemYEe'  # 替换为用户的 secretId
secret_key = 'd33pXAbomtzITkqIyFG4cv77tOK2Tfgc'  # 替换为用户的 secretKey
region = 'ap-nanjing'  # 替换为用户的 Region

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
# 2. 获取客户端对象
client = CosS3Client(config)
# 参照下文的描述。或者参照 Demo 程序，详见 https://github.com/tencentyun/cos-python-sdk-v5/blob/master/qcloud_cos/demo.py
#### 高级上传接口（推荐）
# 根据文件大小自动选择简单上传或分块上传，分块上传具备断点续传功能。
response = client.upload_file(
    Bucket='15108293600-1611374187-1304183991',
    LocalFilePath='1.png',  # 本地文件路径
    Key='p1.png',  # 上传到桶之后的文件名
)
print(response['ETag'])
