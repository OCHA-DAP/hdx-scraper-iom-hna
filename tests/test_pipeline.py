from os.path import join

import pytest
from hdx.api.utilities.hdx_error_handler import HDXErrorHandler
from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from hdx.scraper.iom_hna.pipeline import Pipeline


@pytest.fixture(scope="module")
def expected_tags():
    return [
        {"name": tag, "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"}
        for tag in (
            "displacement",
            "food security",
            "health",
            "internally displaced persons-idp",
            "needs assessment",
            "returnees",
            "shelter",
            "water sanitation and hygiene-wash",
        )
    ]


@pytest.fixture(scope="module")
def expected_dictionary_resource():
    return {
        "name": "iom_dtm_hna_data_dictionary.csv",
        "description": "Data dictionary describing each indicator column in the "
        "IOM DTM Household Needs Assessment resources",
        "format": "csv",
    }


class TestPipeline:
    @pytest.fixture(scope="function")
    def pipeline(self, configuration, input_dir):
        with (
            temp_dir(
                "TestIomHna",
                delete_on_success=True,
                delete_on_failure=False,
            ) as tempdir,
            HDXErrorHandler(write_to_hdx=False) as error_handler,
            Download(user_agent="test") as downloader,
        ):
            retriever = Retrieve(
                downloader=downloader,
                fallback_dir=tempdir,
                saved_dir=input_dir,
                temp_dir=tempdir,
                save=False,
                use_saved=True,
            )
            yield Pipeline(configuration, retriever, tempdir, error_handler, "key")

    def test_get_country_years(self, pipeline):
        assert pipeline.get_country_years() == {
            "SDN": ["2025", "2024", "2022"],
            "SSD": ["2025", "2024", "2023", "2022"],
            "MOZ": ["2025", "2024", "2022"],
            "NGA": ["2022"],
        }

    def test_get_admin2_data(self, pipeline):
        # SSD 2025 has 184 rows over 2 pages
        assert len(pipeline.get_admin2_data("SSD", "2025")) == 184
        # MOZ 2022 has exactly 100 rows on 1 page
        assert len(pipeline.get_admin2_data("MOZ", "2022")) == 100
        # No data: isSuccess true with empty data
        assert pipeline.get_admin2_data("NGA", "2025") == []
        # Error: isSuccess false
        assert pipeline.get_admin2_data("XXX", "2025") == []
        shared_errors = pipeline._error_handler.shared_errors
        assert shared_errors["warning"]["IOM HNA - NGA"] == {
            "IOM HNA - NGA - No data for 2025"
        }
        assert shared_errors["error"]["IOM HNA - XXX"] == {
            (
                "IOM HNA - XXX - 2025 page 1 failed: "
                "['No Country Code found matching your query.']"
            )
        }

    def test_check_columns(self, pipeline):
        row = {"id": 1, "year": 2025, "new_indicator": 1.0}
        pipeline.check_columns("SSD", "2025", row, {"year", "old_indicator"})
        assert pipeline._error_handler.shared_errors["warning"]["IOM HNA - SSD"] == {
            "IOM HNA - SSD - 2025 column new_indicator not in data dictionary",
            "IOM HNA - SSD - 2025 data dictionary indicator old_indicator not in data",
        }

    def test_generate_dataset(
        self,
        pipeline,
        fixtures_dir,
        config_dir,
        expected_tags,
        expected_dictionary_resource,
    ):
        pipeline.setup_admins()
        catalog = pipeline.get_catalog()
        assert len(catalog) == 112

        # MOZ: p-codes matched on names as IOM uses the pre-2025 COD
        dataset = pipeline.generate_dataset("MOZ", ["2025", "2022"], catalog)
        dataset.update_from_yaml(path=join(config_dir, "hdx_dataset_static.yaml"))
        assert dataset["name"] == "moz-iom-dtm-household-needs-assessment"
        assert dataset["title"] == "Mozambique - IOM DTM Household Needs Assessment"
        assert dataset["groups"] == [{"name": "moz"}]
        assert dataset["tags"] == expected_tags
        assert dataset["dataset_date"] == "[2022-01-01T00:00:00 TO 2025-12-31T23:59:59]"
        assert dataset["subnational"] == "1"
        assert dataset["methodology"] == "Sample Survey"
        assert dataset["owner_org"] == "f53d32cd-132c-4ef4-bc6d-058f94d08adf"
        assert dataset["maintainer"] == "196196be-6037-4488-8b71-d786adf4c081"
        assert dataset["data_update_frequency"] == 365
        assert dataset["private"] is False
        assert dataset.get_resources() == [
            {
                "name": f"moz_iom_dtm_hna_{year}.csv",
                "description": "Mozambique IOM DTM Household Needs Assessment "
                f"{year} indicators by admin 2 and population group",
                "p_coded": True,
                "format": "csv",
            }
            for year in ("2025", "2022")
        ] + [expected_dictionary_resource]

        # SSD: Abyei rows keep blank p-codes
        dataset = pipeline.generate_dataset("SSD", ["2025"], catalog)
        assert dataset["dataset_date"] == "[2025-01-01T00:00:00 TO 2025-12-31T23:59:59]"
        assert [resource["name"] for resource in dataset.get_resources()] == [
            "ssd_iom_dtm_hna_2025.csv",
            "iom_dtm_hna_data_dictionary.csv",
        ]
        assert pipeline._error_handler.shared_errors["warning"] == {}

        for filename in (
            "moz_iom_dtm_hna_2025.csv",
            "moz_iom_dtm_hna_2022.csv",
            "ssd_iom_dtm_hna_2025.csv",
            "iom_dtm_hna_data_dictionary.csv",
        ):
            assert_files_same(
                join(fixtures_dir, filename), join(pipeline._tempdir, filename)
            )

    def test_generate_dataset_no_data(self, pipeline):
        assert pipeline.generate_dataset("NGA", ["2025"], []) is None
