class SSHConfig:
    def __init__(self):
        self.configuration = {}

    def add_host(self, name, **kwargs):
        self.configuration[name] = kwargs

    def write(self, config_file):
        lines = []
        for hostname, conf in self.configuration.items():
            lines.append(f"Host {hostname}")
            for key, value in conf.items():
                lines.append(f"\t{key} {value}")

        for line in lines:
            config_file.write(f"{line}\n")
