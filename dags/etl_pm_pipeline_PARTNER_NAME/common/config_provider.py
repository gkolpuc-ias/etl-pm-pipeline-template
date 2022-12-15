from ..common import PMIDAG


class ConfigProvider:
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        dag = PMIDAG.get_dag()
        self.app_name = dag.app_name
        self.env_config = dag.env_config
        self.env_id = dag.env_id

        self.shared_stack = f'etl-pm-shared-{self.env_id}'
        self.prereqs_stack = self._full_stack_name('prereqs')

    def _full_stack_name(self, stack_name) -> str:
        return f'{self.app_name}-{self.env_id}-{stack_name}'

    def aws_resource(self, stack_name: str, resource_name: str) -> str:
        return self.env_config['aws_resources'][stack_name][resource_name]

    def get_shared(self, resource_name: str) -> str:
        return self.aws_resource(self.shared_stack, resource_name)

    def get_prereqs(self, resource_name: str) -> str:
        return self.aws_resource(self.prereqs_stack, resource_name)

