#!/usr/bin/python
"""IOM DTM HNA scraper"""

import logging

from hdx.api.configuration import Configuration
from hdx.api.utilities.hdx_error_handler import HDXErrorHandler
from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.location.adminlevel import AdminLevel
from hdx.location.country import Country
from hdx.pipelineutils.hapi_admins import complete_admins
from hdx.utilities.dateparse import parse_date_range
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)

_PIPELINE = "IOM HNA"


class Pipeline:
    def __init__(
        self,
        configuration: Configuration,
        retriever: Retrieve,
        tempdir: str,
        error_handler: HDXErrorHandler,
        api_key: str | None = None,
    ):
        self._configuration = configuration
        self._retriever = retriever
        self._tempdir = tempdir
        self._error_handler = error_handler
        # Only sent to the HNA API, not to other hosts such as HDX
        self._api_headers = {"Ocp-Apim-Subscription-Key": api_key}
        self._admins = []

    def setup_admins(self) -> None:
        """Set up admin 1 and 2 p-codes from the global p-codes dataset"""
        for admin_level in (1, 2):
            admin = AdminLevel(admin_level=admin_level, retriever=self._retriever)
            admin.setup_from_url()
            admin.load_pcode_formats()
            self._admins.append(admin)

    def get_country_years(self) -> dict[str, list[str]]:
        """Get the years available for each country, newest first"""
        data = self._retriever.download_json(
            self._configuration["COUNTRY_LIST_URL"], headers=self._api_headers
        )["result"]
        country_years = {}
        for country in data:
            years = [year.strip() for year in country["years"].split(",")]
            country_years[country["admin0Pcode"]] = sorted(years, reverse=True)
        return country_years

    def get_catalog(self) -> list[dict]:
        """Get the data dictionary describing each indicator column"""
        return self._retriever.download_json(
            self._configuration["CATALOG_URL"], headers=self._api_headers
        )

    def get_admin2_data(self, iso3: str, year: str) -> list[dict]:
        """Get all pages of admin 2 data for a country and year. Returns an
        empty list if the API reports an error, so that a year is never
        published with partial data."""
        rows = []
        page = 1
        while True:
            url = self._configuration["ADMIN2_URL"].format(
                iso3=iso3, year=year, page=page
            )
            response = self._retriever.download_json(
                url,
                filename=f"admin2_{iso3.lower()}_{year}_page_{page}.json",
                headers=self._api_headers,
            )
            if not response.get("isSuccess"):
                self._error_handler.add_message(
                    _PIPELINE,
                    iso3,
                    f"{year} page {page} failed: {response.get('errorMessages')}",
                )
                return []
            result = response["result"]
            rows.extend(result["data"])
            if not result["pagination"]["hasNextPage"]:
                break
            page += 1
        if not rows:
            self._error_handler.add_message(
                _PIPELINE, iso3, f"No data for {year}", message_type="warning"
            )
        return rows

    def check_columns(
        self, iso3: str, year: str, row: dict, indicator_names: set[str]
    ) -> None:
        """Log any difference between the data columns and the data dictionary"""
        columns = set(row) - set(self._configuration["non_indicator_columns"])
        for column in sorted(columns - indicator_names):
            self._error_handler.add_message(
                _PIPELINE,
                iso3,
                f"{year} column {column} not in data dictionary",
                message_type="warning",
            )
        for indicator_name in sorted(indicator_names - columns):
            self._error_handler.add_message(
                _PIPELINE,
                iso3,
                f"{year} data dictionary indicator {indicator_name} not in data",
                message_type="warning",
            )

    def get_standard_admins(self, iso3: str, row: dict) -> tuple[list, list]:
        """Get admin 1 and 2 p-codes and names from the current COD, using the
        provider's p-codes where they can be trusted and names otherwise"""
        columns = self._configuration["provider_admin_columns"]
        provider_names = [
            row[columns["admin1_name"]] or "",
            row[columns["admin2_name"]] or "",
        ]
        if provider_names[1] in self._configuration["no_pcode_admin_names"]:
            return ["", ""], ["", ""]
        if iso3 in self._configuration["ignore_provider_pcodes"]:
            pcodes = ["", ""]
        else:
            pcodes = [
                row[columns["admin1_pcode"]] or "",
                row[columns["admin2_pcode"]] or "",
            ]
        names = ["", ""]
        _, warnings = complete_admins(self._admins, iso3, provider_names, pcodes, names)
        for warning in warnings:
            self._error_handler.add_message(
                _PIPELINE, iso3, warning, message_type="warning"
            )
        if not pcodes[1]:
            self._error_handler.add_message(
                _PIPELINE,
                iso3,
                f"No admin 2 p-code for {provider_names[0]}/{provider_names[1]}",
                message_type="warning",
            )
        return pcodes, names

    def process_row(self, iso3: str, row: dict) -> dict:
        """Keep the provider's columns and add standard admin and date columns
        after the provider's admin 2 p-code column"""
        pcodes, names = self.get_standard_admins(iso3, row)
        startdate, enddate = parse_date_range(
            str(row[self._configuration["year_column"]])
        )
        standard_values = {
            "admin1_pcode": pcodes[0],
            "admin1_name": names[0],
            "admin2_pcode": pcodes[1],
            "admin2_name": names[1],
            "reference_period_start": startdate.strftime("%Y-%m-%d"),
            "reference_period_end": enddate.strftime("%Y-%m-%d"),
        }
        insert_after = self._configuration["provider_admin_columns"]["admin2_pcode"]
        new_row = {}
        for key, value in row.items():
            if isinstance(value, str):
                value = value.strip()
            new_row[key] = value
            if key == insert_after:
                for column in self._configuration["standard_columns"]:
                    new_row[column] = standard_values[column]
        return new_row

    def generate_dataset(
        self, iso3: str, years: list[str], catalog: list[dict]
    ) -> Dataset | None:
        country_name = Country.get_country_name_from_iso3(iso3)
        dataset_name = f"{iso3.lower()}-iom-dtm-household-needs-assessment"
        dataset = Dataset(
            {
                "name": dataset_name,
                "title": f"{country_name} - IOM DTM Household Needs Assessment",
            }
        )
        try:
            dataset.add_country_location(iso3)
        except HDXError:
            logger.error(f"Couldn't find country {iso3}, skipping")
            return None
        dataset.add_tags(self._configuration["tags"])
        dataset.set_subnational(True)

        indicator_names = {indicator["indicator_name"] for indicator in catalog}
        dataset_years = []
        for year in years:
            rows = self.get_admin2_data(iso3, year)
            if not rows:
                continue
            self.check_columns(iso3, year, rows[0], indicator_names)
            rows = [self.process_row(iso3, row) for row in rows]
            filename = f"{iso3.lower()}_iom_dtm_hna_{year}.csv"
            dataset.generate_resource(
                folder=self._tempdir,
                filename=filename,
                rows=rows,
                resourcedata={
                    "name": filename,
                    "description": f"{country_name} IOM DTM Household Needs "
                    f"Assessment {year} indicators by admin 2 and population group",
                    "p_coded": True,
                },
                headers=list(rows[0]),
                encoding="utf-8-sig",
            )
            dataset_years.append(year)
        if not dataset_years:
            logger.error(f"No data for {iso3}, skipping")
            return None

        filename = self._configuration["catalog_resource_filename"]
        dataset.generate_resource(
            folder=self._tempdir,
            filename=filename,
            rows=catalog,
            resourcedata={
                "name": filename,
                "description": self._configuration["catalog_resource_description"],
            },
            headers=self._configuration["catalog_headers"],
            encoding="utf-8-sig",
        )
        startdate, _ = parse_date_range(min(dataset_years))
        _, enddate = parse_date_range(max(dataset_years))
        dataset.set_time_period(startdate, enddate)
        return dataset
