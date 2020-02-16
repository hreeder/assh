import boto3
import botostubs
import pytest

from moto.ec2 import mock_ec2

PUBLIC_INSTANCE_NAME = "Public Instance"
PRIVATE_INSTANCE_NAME = "Private Instance"
INSTANCE_TYPE = "t3.micro"
IMAGE_NAME = "ami-assh-test-1"
KEY_NAME = "testkey"

DEFAULT_INSTANCE_KWARGS = {
    "MaxCount": 1,
    "MinCount": 1,
    "InstanceType": INSTANCE_TYPE,
    "KeyName": KEY_NAME,
}


@pytest.fixture(name="ec2", scope="session")
def ec2():
    with mock_ec2():
        yield boto3.client("ec2")


@pytest.fixture(name="vpc", scope="session")
def fxt_vpc(ec2: botostubs.EC2):
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16", DryRun=False)

    yield vpc["Vpc"]


@pytest.fixture(name="public_subnet", scope="session")
def fxt_public_subnet(ec2: botostubs.EC2, vpc):
    subnet = ec2.create_subnet(VpcId=vpc["VpcId"], CidrBlock="10.0.0.0/24")
    ec2.modify_subnet_attribute(
        SubnetId=subnet["Subnet"]["SubnetId"], MapPublicIpOnLaunch={"Value": True}
    )

    yield subnet["Subnet"]


@pytest.fixture(name="private_subnet", scope="session")
def fxt_private_subnet(ec2: botostubs.EC2, vpc):
    subnet = ec2.create_subnet(VpcId=vpc["VpcId"], CidrBlock="10.0.1.0/24")

    yield subnet["Subnet"]


@pytest.fixture(name="ami_amzn", scope="session")
def fxt_ami_amzn(ec2: botostubs.EC2, public_subnet):
    instance = ec2.run_instances(**DEFAULT_INSTANCE_KWARGS, ImageId=IMAGE_NAME)
    instance_id = instance["Instances"][0]["InstanceId"]

    image = ec2.create_image(
        Description="Mock Amazon Linux Image",
        Name="mock_amazon_linux",
        InstanceId=instance_id,
    )
    yield image


@pytest.fixture(name="ami_ubuntu", scope="session")
def fxt_ami_ubuntu(ec2: botostubs.EC2, public_subnet):
    instance = ec2.run_instances(**DEFAULT_INSTANCE_KWARGS, ImageId=IMAGE_NAME)
    instance_id = instance["Instances"][0]["InstanceId"]

    image = ec2.create_image(
        Description="Mock Ubuntu Linux Image",
        Name="mock_ubuntu_linux",
        InstanceId=instance_id,
    )
    yield image


@pytest.fixture(name="ami_centos", scope="session")
def fxt_ami_centos(ec2: botostubs.EC2, public_subnet):
    instance = ec2.run_instances(**DEFAULT_INSTANCE_KWARGS, ImageId=IMAGE_NAME)
    instance_id = instance["Instances"][0]["InstanceId"]

    image = ec2.create_image(
        Description="Mock CentOS Linux Image",
        Name="mock_centos_linux",
        InstanceId=instance_id,
    )
    yield image


@pytest.fixture(name="public_aws_instance", scope="session")
def fxt_public_aws_instance(ec2: botostubs.EC2, public_subnet, ami_amzn):
    new_instance = ec2.run_instances(
        **DEFAULT_INSTANCE_KWARGS,
        ImageId=ami_amzn["ImageId"],
        SubnetId=public_subnet["SubnetId"],
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": PUBLIC_INSTANCE_NAME}],
            }
        ],
    )
    instance_id = new_instance["Instances"][0]["InstanceId"]
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    yield instances["Reservations"][0]["Instances"][0]


@pytest.fixture(name="private_aws_instance", scope="session")
def fxt_private_aws_instance(ec2: botostubs.EC2, private_subnet, ami_ubuntu):
    new_instance = ec2.run_instances(
        **DEFAULT_INSTANCE_KWARGS,
        ImageId=ami_ubuntu["ImageId"],
        SubnetId=private_subnet["SubnetId"],
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": PRIVATE_INSTANCE_NAME}],
            }
        ],
    )
    instance_id = new_instance["Instances"][0]["InstanceId"]
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    yield instances["Reservations"][0]["Instances"][0]


@pytest.fixture(name="terminated_aws_instance", scope="session")
def fxt_terminated_aws_instance(ec2: botostubs.EC2, public_subnet, ami_amzn):
    new_instance = ec2.run_instances(
        **DEFAULT_INSTANCE_KWARGS,
        ImageId=ami_amzn["ImageId"],
        SubnetId=public_subnet["SubnetId"],
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "Terminated Instance"}],
            }
        ],
    )
    instance_id = new_instance["Instances"][0]["InstanceId"]
    ec2.terminate_instances(InstanceIds=[instance_id])
