# assh
`assh` is a command-line utility to make it easy to SSH to your AWS EC2 Instances.

## Installation
At the current time, this package is only installable from source.

`pip install -e git+https://github.com/hreeder/assh.git@master#egg=assh` will install `assh` plus dependencies.

Alternatively, clone this repo and run `pip install .` from within the repository.


## Usage
```
» assh --help
Usage: assh [OPTIONS] [QUERY]...

Options:
  --log-level TEXT          Set log level
  -m, --mode TEXT           Connection mode (ssh, ssm, ssm-ssh)
  -v, --via TEXT            Proxy SSH via host
  -l, --login_name TEXT     EC2 Instance Username Override
  -i, --identity_file TEXT  SSH Private Key
  --help                    Show this message and exit.
```

Basic usage can be with `assh i-abc123def`, however `assh` will search based on the Name tag as well, so if instance `i-abc123def` has a name of `Target`, `assh target` would allow connection.

### Parameters
* `-m` / `--mode`: Valid values: `ssh`, `ssm`, `ssm-ssh`:
  * `ssh`: This creates a plain SSH connection. (**Default**)
  * `ssm`: This starts a session using SSM Session Manager. This **does not** utilise SSH at all.
  * `ssm-ssh`: This will cause the SSH connection to be proxied over SSM's Session manager.
  * Both `ssm` and `ssm-ssh` have an extra dependency on your system having `awscli` and `session-manager-plugin` both configured.
* `-v` / `--via`: This allows you to use a given instance as a jump host to get to the final destination, ie `assh --via i-789def123 i-123abcdef` will cause the connection to get routed like so: `Client ---> i-789def123 --> i-123abcdef`. This parameter supports tab completion if [configured](#autocompletion).
* `-l` / `--login_name`: This allows you to override the default username resolution functionality with a given name.
* `-i` / `--identity_file`: This allows you to set your SSH private key.

### Configuration
`assh` can be configured from a YAML file as well. Create `~/.assh/config.yaml` with the following content:
```
---
default-key: ~/.ssh/id_aws
default-keypairs:
  standard: ~/.ssh/id_other_aws
profiles:
  aws-profile-top-secret:
    top-secret-keypair: ~/.ssh/id_top_secret
global-username-patterns:
- username: fred
  image-name: .*
username-patterns:
  aws-profile-top-secret:
  - username: foo
    image-name: bar
  - username: baz
    description: qux
```

* `default-key` allows a default private key to be supplied.
* `default-keypairs` is a mapping of keypair names to private key locations on the local filesystem. "Keypair names" refers to the name visibile in the AWS console/API when describing an instance (or use `aws ec2 describe-key-pairs` and reference the `KeyName` value.)
* `profiles` allows for mapping of specific keypairs (like in the `default-keypairs` section), but per locally configured AWS profile. This means you can have a profile configured as `[profile aws-profile-top-secret]` in your `~/.aws/config`, and the above config file would map `top-secret-keypair` to `~/.ssh/id_top_secret` only for that AWS profile.
* `global-username-patterns` allows the default username resolution to be extended with a custom set of patterns. Each entry in the list MUST have a `username` field, and can have an `image-name`, or a `description` field.
* `username-patterns` allows for the same mapping to exist, but on a per-AWS profile name, similar to the `profiles` section above. (In future these two sections should be merged, but to preserve compatibility they are not being merged at the corrent time)

## Autocompletion
* Bash: `eval "$(_ASSH_COMPLETE=source assh)"`
* Zsh: `eval "$(_ASSH_COMPLETE=source_zsh assh)"`
