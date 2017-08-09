# swag_client

![PyPi](http://img.shields.io/pypi/v/swag-client.svg?style=flat)

![Build Status](https://travis-ci.org/Netflix-Skunkworks/swag-client.svg?branch=master)

![OSS Status](https://img.shields.io/badge/NetflixOSS-active-brightgreen.svg)


SWAG is a collection of repositories used to keep track of the metadata describing cloud accounts.  Originally built to store data on AWS, swag is flexible enough to be used for multiple providers (AWS, GCP, etc.,).

For applications that manage or deploy to several different accounts/environments SWAG provides a centralized metadata store.

Managing your cloud accounts with SWAG allows for consuming application to focus on business logic, removing hardcoded lists or properties from your application.


## Installation

swag-client is available on pypi:

```bash
    pip install swag-client
```


## Basic Usage
If no options are passed to the SWAGManager it is assumed that you are using the `file` backend and the `account` namespace.

```python
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {}
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = swag.get_by_name('account')
```

Configure SWAG by passing the client additional keyword arguments:

```python
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
```

### Filtering

Regardless of backend, SWAG uses the `jmespath` syntax for filtering data.

```python
    swag.get("[?id=='012345678910']")  # valid jmespath filter
```

More information on jmespath filtering: http://jmespath.org/tutorial.html

### Old-style

SWAG also supports an older style calling convention. This convention only supports the S3 backend, additionally these functions are now deprecated and will be removed in the future.

```python
    from swag_client.swag import get_all_accounts
    get_all_accounts(bucket='your-swag-bucket').get('accounts')
```

or to filter by a service tag:

```python
    service = {'services': {'YOURSERVICE': {'enabled': True, 'randomflag': True}}}
    get_all_accounts(bucket='your-swag-bucket', **service).get('accounts')
```

## Versioning

All SWAG metadata is versioned. The most current version of the `account` metadata schema is v2. SWAG further provides the ability to transform data between schema version as necessary.

## Backends

SWAG supports multiple backends, included in the package are file, s3, and dynamodb backends. Additional backends can easily be created and integrated into SWAG.


#### Global Backend Options

| Key | Type | Required | Description |
| --- | ---- | -------- | ----------- |
| swag.type | str | false | Type of backend to use (Default: 'file') |
| swag.namespace | str | false | Namespace for metadata (Default: 'accounts') |


### S3 Backend

The S3 backend uses AWS S3 to SWAG metadata.

#### Backend Options

| Key | Type | Required | Description |
| --- | ---- | -------- | ----------- |
| swag.bucket_name | str | true | Raw S3 bucket name |
| swag.data_file | str | false | Full S3 key of file |
| swag.region | str | false | Region the bucket exists in. (Default: us-east-1)


#### Permissions

IAM Permissions required:

```
    {
        "Action": ["s3:GetObject"],
        "Effect": ["Allow"],
        "Resource: ["arn:aws:s3:::<swag-bucket-name>/<data-file>"]
    }
```

If you wish to update SWAG metadata you will also need the following permissions:

```
    {
        "Action": ["s3:PutObject"],
        "Effect": ["Allow"],
        "Resource: ["arn:aws:s3:::<swag-bucket-name>/<data-file>"]
    }
```


### File Backend
The file backend uses a file on the local filesystem. This backend is often useful for testing purposes but it not scalable to multiple clients.


#### Backend Options
| Key | Type | Required | Description |
| --- | ---- | -------- | ----------- |
| swag.data_dir | str | false | Directory to store data (Default: cwd()) |
| swag.data_file | str | false | Full path to data file |


### DynamoDB Backend
The DynamoDB backend leverages AWSs DynamoDB as a key value store for SWAG metadata.

#### Backend Options

| Key | Type | Required | Description |
| --- | ---- | -------- | ----------- |
| swag.key_attribute | str | false | Unique attribute key |
| swag.key_type | str | false | Type of attribute key (typically HASH) |
| swag.region | str | false | Region dynamodb table exists |
| swag.read_units | int | false | Number of read units (Default: 1) |
| swag.write_units | int | false | Number of write units (Default: 1) |

Note the above options except region is only needed if not SWAG table has been created.

#### Permissions

Minimum Permissions required:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DescribeQueryTable",
            "Effect": "Allow",
            "Action": [
                "dynamodb:DescribeTable",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "*"
        }
    ]
}
```

If you wish SWAG to modify your table you will need the following additional permissions:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PutUpdateDeleteTable",
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "*"
        }
    ]
}
```

If you wish for SWAG to create your table if it does not exist you will need the following additional permissions:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PutUpdateDeleteTable",
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable"
            ],
            "Resource": "*"
        }
    ]
}
```


### CLI Usage

Upon installation the swag_client creates a `swag` entrypoint which invokes the swag_client cli, example usage:

Examples:

```bash
    swag create <path-to-data> --bucket-name swag.test.com
```


```bash
    swag validate <path-to-data> --verison 1
```


```bash
    swag list --bucket-name swag.test.com
```

Additional documentation available via:
```bash
    swag --help
```


Additional Projects:
These projects are part of the SWAG family and either manipulate or utilize SWAG data.


See [sample_accounts.json](https://github.com/Netflix-Skunkworks/swag-client/blob/master/sample_accounts.json) an example of the current json data created by SWAG.

