from typing import List

import boto3


class Instance:
    def __init__(self, aws_instance):
        self.id = aws_instance["InstanceId"]
        self.state = aws_instance["State"]["Name"]
        self.type = aws_instance["InstanceType"]
        self.image = aws_instance["ImageId"]

        # Keyname is optional as to support SSM-only access where instances
        # may not have an attached keyname
        self.keyname = aws_instance.get("KeyName")

        self.private_ip = aws_instance["PrivateIpAddress"]
        self.public_ip = aws_instance.get("PublicIpAddress")

        self.tags = {
            pair["Key"]: pair["Value"] for pair in aws_instance.get("Tags", [])
        }

    @property
    def name(self):
        return self.tags.get("Name", "")

    def to_dict(self):
        return {
            "id": self.id,
            "state": self.state,
            "type": self.type,
            "image": self.image,
            "keyname": self.keyname,
            "private_ip": self.private_ip,
            "public_ip": self.public_ip,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, instance_dict):
        return cls(
            {
                "InstanceId": instance_dict["id"],
                "State": {"Name": instance_dict["state"]},
                "InstanceType": instance_dict["type"],
                "ImageId": instance_dict["image"],
                "KeyName": instance_dict["keyname"],
                "PrivateIpAddress": instance_dict["private_ip"],
                "PublicIpAddress": instance_dict["public_ip"],
                "Tags": [
                    {"Key": key, "Value": value}
                    for key, value in instance_dict["tags"].items()
                ],
            }
        )

    def default_username(self) -> str:
        ec2 = boto3.client("ec2")
        images = ec2.describe_images(ImageIds=[self.image])
        image = images["Images"][0]
        # Some images come back without a Description key
        description = image.get("Description", "").lower()

        if "ubuntu" in description:
            return "ubuntu"

        if "centos" in description:
            return "centos"

        return "ec2-user"  # Default to amazon linux / RHEL default username


def get_instances() -> List[Instance]:
    ec2 = boto3.client("ec2")
    instances = ec2.describe_instances()

    instances = [
        instance
        for r in instances["Reservations"]
        for instance in r["Instances"]
        if instance["State"]["Name"] == "running"
    ]
    return [Instance(instance) for instance in instances]
