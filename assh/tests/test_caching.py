"""Tests the caching functionality"""
import datetime
import json
import unittest.mock

from pathlib import Path

import botostubs
import pytest

import assh.caching

from assh.caching import get_instances, get_instance
from assh.exceptions import TooManyResultsException, NoResultsException
from assh.instance import Instance


@pytest.fixture(name="cache_dir")
def fxt_cache_dir(tmp_path: Path):
    cache_dir = tmp_path / "assh-cache"
    cache_dir.mkdir()
    return cache_dir


def test_get_instances_caches_result(
    ec2: botostubs.EC2, cache_dir: Path, mocker, public_aws_instance
):
    expected_path = cache_dir / "instances-default.json"

    assert not expected_path.exists()

    spy_fresh_instances: unittest.mock.MagicMock = mocker.spy(
        assh.caching, "_get_fresh_instances"
    )

    instances = get_instances(cache_dir)

    assert expected_path.exists()
    assert type(instances[0]) == Instance

    cache = {}
    with open(expected_path) as cache_file:
        cache = json.load(cache_file)

    assert "fetched_at" in cache
    assert "instances" in cache

    assert type(cache["fetched_at"]) == float
    datetime.datetime.fromtimestamp(cache["fetched_at"])

    # Expected that this will get from cache
    cached_instances = get_instances(cache_dir)

    # Test that the casting works when retreiving from cache
    assert type(cached_instances[0]) == Instance

    spy_fresh_instances.assert_called_once()


def test_get_specific_instance(
    ec2: botostubs.EC2, cache_dir: Path, public_aws_instance, private_aws_instance
):
    """Test retrieval of specific instances by name queries."""
    public_instance = get_instance(cache_dir, "public")
    private_instance = get_instance(cache_dir, "private")

    assert public_instance.id == public_aws_instance["InstanceId"]
    assert private_instance.id == private_aws_instance["InstanceId"]


def test_get_specific_instance_by_id(
    ec2: botostubs.EC2, cache_dir: Path, public_aws_instance, private_aws_instance
):
    """Test retrieval of specific instances by ID queries."""
    public_instance = get_instance(cache_dir, public_aws_instance["InstanceId"])
    private_instance = get_instance(cache_dir, private_aws_instance["InstanceId"])

    assert public_instance.id == public_aws_instance["InstanceId"]
    assert private_instance.id == private_aws_instance["InstanceId"]


def test_too_broad(ec2: botostubs.EC2, cache_dir: Path):
    """Tests exception is raised when too broad a query is searched for."""
    with pytest.raises(TooManyResultsException):
        get_instance(cache_dir, "i-")


def test_too_specific(ec2: botostubs.EC2, cache_dir: Path):
    """Tests exception is raised when no results were found."""
    with pytest.raises(NoResultsException):
        get_instance(cache_dir, "Lorem Ipsum Dolor Sit Amet")
