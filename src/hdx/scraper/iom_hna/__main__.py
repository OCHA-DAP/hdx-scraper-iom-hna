#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this
script then creates in HDX.

"""

import logging
from os import getenv
from os.path import expanduser, join

from hdx.api.configuration import Configuration
from hdx.api.utilities.hdx_error_handler import HDXErrorHandler
from hdx.data.user import User
from hdx.facades.infer_arguments import facade
from hdx.utilities.downloader import Download
from hdx.utilities.path import (
    script_dir_plus_file,
    wheretostart_tempdir_batch,
)
from hdx.utilities.retriever import Retrieve

from hdx.scraper.iom_hna._version import __version__
from hdx.scraper.iom_hna.pipeline import Pipeline

logger = logging.getLogger(__name__)

_LOOKUP = "hdx-scraper-iom-hna"
_SAVED_DATA_DIR = "saved_data"  # Keep in repo to avoid deletion in /tmp
_UPDATED_BY_SCRIPT = "HDX Scraper: IOM DTM HNA"


def main(
    dtm_hna_key: str | None = None,
    save: bool = False,
    use_saved: bool = False,
    err_to_hdx: bool | None = None,
) -> None:
    """Generate datasets and create them in HDX

    Args:
        dtm_hna_key: IOM DTM HNA API key. Defaults to DTM_HNA_KEY env var.
        save: Save downloaded data. Defaults to False.
        use_saved: Use saved data. Defaults to False.
        err_to_hdx: Whether to write any errors to HDX metadata. Defaults to None.

    Returns:
        None
    """
    logger.info(f"##### {_LOOKUP} version {__version__} ####")
    if dtm_hna_key is None:
        dtm_hna_key = getenv("DTM_HNA_KEY")
    if err_to_hdx is None:
        err_to_hdx = getenv("ERR_TO_HDX")
    configuration = Configuration.read()
    User.check_current_user_write_access("f53d32cd-132c-4ef4-bc6d-058f94d08adf")

    with (
        HDXErrorHandler(write_to_hdx=err_to_hdx) as error_handler,
        wheretostart_tempdir_batch(folder=_LOOKUP) as info,
        Download() as downloader,
    ):
        tempdir = info["folder"]
        retriever = Retrieve(
            downloader=downloader,
            fallback_dir=tempdir,
            saved_dir=_SAVED_DATA_DIR,
            temp_dir=tempdir,
            save=save,
            use_saved=use_saved,
        )
        pipeline = Pipeline(
            configuration, retriever, tempdir, error_handler, dtm_hna_key
        )
        pipeline.setup_admins()
        catalog = pipeline.get_catalog()
        for iso3, years in pipeline.get_country_years().items():
            try:
                dataset = pipeline.generate_dataset(iso3, years, catalog)
                if not dataset:
                    continue
                dataset.update_from_yaml(
                    script_dir_plus_file(
                        join("config", "hdx_dataset_static.yaml"), main
                    )
                )
                dataset.create_in_hdx(
                    remove_additional_resources=True,
                    match_resource_order=True,
                    updated_by_script=_UPDATED_BY_SCRIPT,
                    batch=info["batch"],
                )
            except Exception:
                logger.exception(f"Failed to process {iso3}")
                error_handler.add_message(
                    "IOM HNA", iso3, "Failed to generate or create dataset"
                )
    logger.info("HDX Scraper IOM DTM HNA pipeline completed!")


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_LOOKUP,
        project_config_yaml=script_dir_plus_file(
            join("config", "project_configuration.yaml"), main
        ),
    )
