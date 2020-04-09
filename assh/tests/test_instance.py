"""Test instance class."""
import botostubs

from pprint import pprint

from assh.instance import Instance, get_instances

from assh.tests.conftest import (
    DEFAULT_INSTANCE_KWARGS,
    IMAGE_NAME,
    INSTANCE_TYPE,
    KEY_NAME,
    PUBLIC_INSTANCE_NAME,
)


def test_data_extraction(public_aws_instance, ami_amzn):
    """Test extraction of data from AWS format."""
    instance = Instance(public_aws_instance)

    assert instance.id == public_aws_instance["InstanceId"]
    assert instance.private_ip == public_aws_instance["PrivateIpAddress"]
    assert instance.public_ip == public_aws_instance["PublicIpAddress"]
    assert instance.state == public_aws_instance["State"]["Name"]
    assert instance.type == INSTANCE_TYPE
    assert instance.image == ami_amzn["ImageId"]
    assert instance.keyname == KEY_NAME


def test_name_extraction(public_aws_instance):
    """Test extraction of Name from tags of an instance."""
    instance = Instance(public_aws_instance)

    assert instance.name == PUBLIC_INSTANCE_NAME


def test_serialisation(public_aws_instance, ami_amzn):
    """Test serialisation of Instance class to dictionary."""
    instance = Instance(public_aws_instance)

    assert instance.to_dict() == {
        "id": public_aws_instance["InstanceId"],
        "private_ip": public_aws_instance["PrivateIpAddress"],
        "public_ip": public_aws_instance["PublicIpAddress"],
        "state": public_aws_instance["State"]["Name"],
        "type": INSTANCE_TYPE,
        "image": ami_amzn["ImageId"],
        "keyname": KEY_NAME,
        "tags": {"Name": PUBLIC_INSTANCE_NAME},
    }


def test_deserialisation():
    """Test deserialisation of Instance class from dictionary."""
    instance_dict = {
        "id": "i-123abc",
        "private_ip": "10.0.0.1",
        "public_ip": "1.2.3.4",
        "state": "running",
        "type": INSTANCE_TYPE,
        "image": IMAGE_NAME,
        "keyname": KEY_NAME,
        "tags": {"Name": PUBLIC_INSTANCE_NAME},
    }

    instance = Instance.from_dict(instance_dict)
    assert instance.to_dict() == instance_dict


def test_parse_private_instance(private_aws_instance):
    """Test parsing of a private instance (without a public IP)."""
    instance = Instance(private_aws_instance)

    assert instance.public_ip == None


def test_all_instance_retrieval(ec2: botostubs.EC2):
    """Tests getting all instances."""
    instances = get_instances()

    assert type(instances) == list
    assert type(instances[0]) == Instance


def test_amazon_linux_username_retrieval(
    ec2: botostubs.EC2, ami_amzn, public_aws_instance
):
    """Tests username resolution expecting ec2-user."""
    instance = Instance(public_aws_instance)

    assert instance.default_username() == "ec2-user"


def test_ubuntu_username_retrieval(
    ec2: botostubs.EC2, ami_ubuntu, private_aws_instance
):
    """Tests username resolution expecting ubuntu."""
    instance = Instance(private_aws_instance)

    assert instance.default_username() == "ubuntu"


def test_centos_username_retreival(ec2: botostubs.EC2, ami_centos, public_subnet):
    """Tests username resolution expecting centos."""
    new_centos_instance = ec2.run_instances(
        **DEFAULT_INSTANCE_KWARGS,
        ImageId=ami_centos["ImageId"],
        SubnetId=public_subnet["SubnetId"],
    )
    instance_id = new_centos_instance["Instances"][0]["InstanceId"]
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = Instance(instances["Reservations"][0]["Instances"][0])

    assert instance.default_username() == "centos"


def test_no_description_username_fallback(
    ec2: botostubs.EC2, ami_custom, public_subnet
):
    """Tests username resolution expecting the default fallback to ec2-user."""
    new_instance = ec2.run_instances(
        **DEFAULT_INSTANCE_KWARGS,
        ImageId=ami_custom["ImageId"],
        SubnetId=public_subnet["SubnetId"],
    )
    instance_id = new_instance["Instances"][0]["InstanceId"]
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = Instance(instances["Reservations"][0]["Instances"][0])

    assert instance.default_username() == "ec2-user"


def test_handles_terminated_instances_gracefully(
    ec2: botostubs.EC2, terminated_aws_instance
):
    """Tests that no failures are encountered when parsing terminated instances."""
    get_instances()
