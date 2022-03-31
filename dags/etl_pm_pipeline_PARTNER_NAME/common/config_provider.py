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
        self.viewability_stack = self._full_stack_name('viewability-marting')
        self.brandsafety_stack = self._full_stack_name('brand-safety-marting')
        self.adh_downloader_stack = self._full_stack_name('adh-downloader')
        self.customer_links_builder_stack = self._full_stack_name('customer-links-builder')
        self.metadata_extractor_stack = self._full_stack_name('metadata-extractor')
        self.snowflake_csv_extractor_stack = self._full_stack_name('snowflake-exporter')
        self.video_content_fetcher_stack = self._full_stack_name('video-content-fetcher')
        self.premart_queries_runner = self._full_stack_name('premart-queries-runner')

    def _full_stack_name(self, stack_name) -> str:
        return f'{self.app_name}-{self.env_id}-{stack_name}'

    def aws_resource(self, stack_name: str, resource_name: str) -> str:
        return self.env_config['aws_resources'][stack_name][resource_name]

    def get_shared(self, resource_name: str) -> str:
        return self.aws_resource(self.shared_stack, resource_name)

    def get_prereqs(self, resource_name: str) -> str:
        return self.aws_resource(self.prereqs_stack, resource_name)

    def get_viewability(self, resource_name: str) -> str:
        return self.aws_resource(self.viewability_stack, resource_name)

    def get_brandsafety(self, resource_name: str) -> str:
        return self.aws_resource(self.brandsafety_stack, resource_name)

    def get_customer_links_builder(self, resource_name: str) -> str:
        return self.aws_resource(self.customer_links_builder_stack, resource_name)

    def get_adh_downloader(self, resource_name: str) -> str:
        return self.aws_resource(self.adh_downloader_stack, resource_name)

    def get_metadata_extractor(self, resource_name: str) -> str:
        return self.aws_resource(self.metadata_extractor_stack, resource_name)

    def get_snowflake_extractor(self, resource_name: str) -> str:
        return self.aws_resource(self.snowflake_csv_extractor_stack, resource_name)

    def get_video_content_fetcher(self, resource_name: str) -> str:
        return self.aws_resource(self.video_content_fetcher_stack, resource_name)

    def get_premart_queries_runner(self, resource_name: str) -> str:
        return self.aws_resource(self.premart_queries_runner, resource_name)
