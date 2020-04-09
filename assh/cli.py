#!/usr/bin/env python3
import datetime
import json
import logging
import os
import random
import string
import subprocess

from pathlib import Path
from pprint import pprint

import boto3
import click
import yaml

from .ssh_config import SSHConfig
from .caching import get_instance, get_instances

TOOL_DIR = Path.home() / ".assh"

CONFIG_PATH = TOOL_DIR / "config.yaml"
CACHE_DIR = TOOL_DIR / "cache"


def _autocomplete_instances(ctx, args, incomplete):
    autocomplete = [
        (instance.id, instance.name) for instance in get_instances(CACHE_DIR)
    ]
    return [
        (instance.id, instance.name)
        for instance in get_instances(CACHE_DIR)
        if (incomplete in instance.id or incomplete.lower() in instance.name.lower())
    ]


@click.command()
@click.argument("query", nargs=-1, autocompletion=_autocomplete_instances)
@click.option("--log-level", required=False, default="warning", help="Set log level")
# @click.option("--region", required=False, help="AWS Region")
@click.option(
    "-m", "--mode", default="ssh", help="Connection mode (ssh, ssm, ssm-ssh)",
)
@click.option(
    "-v",
    "--via",
    required=False,
    help="Proxy SSH via host",
    autocompletion=_autocomplete_instances,
)
@click.option(
    "-l", "--login_name", required=False, help="EC2 Instance Username Override"
)
@click.option("-i", "--identity_file", required=False, help="SSH Private Key")
def main(query, log_level, mode, via, login_name, identity_file):
    logging.basicConfig(level=log_level.upper())

    query = " ".join(query)
    instance = get_instance(CACHE_DIR, query)

    sshconf = SSHConfig()
    dest_kwargs = {"HostName": instance.public_ip}

    current_aws_profile = os.environ.get(
        "AWS_PROFILE", os.environ.get("AWS_DEFAULT_PROFILE")
    )

    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as config_file:
            config = yaml.load(config_file, Loader=yaml.SafeLoader)

    if mode == "ssm":
        start_session = ["aws", "ssm", "start-session", "--target", instance.id]
        logging.info(
            "Attempting to connect using command '%s'", " ".join(start_session)
        )
        subprocess.run(start_session)
        return

    # Username
    resolved_username = login_name if login_name else instance.default_username()
    logging.info("Resolved username as '%s'", resolved_username)
    dest_kwargs["User"] = resolved_username

    # Private Key
    if identity_file:
        key_path = identity_file
    else:
        key_path = (
            (
                config.get("profiles", {})
                .get(current_aws_profile, {})
                .get(instance.keyname)
            )
            or config.get("default-keypairs", {}).get(instance.keyname)
            or config.get("default-key")
        )

    if key_path:
        dest_kwargs["IdentityFile"] = key_path

    # Jump Host
    if via:
        dest_kwargs["HostName"] = instance.private_ip
        via_instance = get_instance(CACHE_DIR, via)
        via_username = login_name if login_name else via_instance.default_username()
        sshconf.add_host(
            "jump",
            HostName=via_instance.public_ip,
            User=via_username,
            IdentityFile=key_path,
        )
        dest_kwargs["ProxyJump"] = "jump"

    # SSM Support
    if mode == "ssm-ssh":
        dest_kwargs["HostName"] = instance.id
        dest_kwargs[
            "ProxyCommand"
        ] = "sh -c \"aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'\""

    logging.info("Creating SSH Configuration with %s", dest_kwargs)
    sshconf.add_host("destination", **dest_kwargs)

    suffix = "".join(random.choice(string.ascii_lowercase) for _ in range(6))
    conf_path = TOOL_DIR / f".sshconf-{suffix}"
    with open(conf_path, "w+") as conf_file:
        sshconf.write(conf_file)

    ssh_command = ["ssh", "-F", str(conf_path), "destination"]

    logging.info("Attempting to connect using command '%s'", " ".join(ssh_command))
    subprocess.run(ssh_command)

    os.remove(conf_path)
