import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import update_latest_headlines
from scripts.update_latest_headlines import parse_homepage_key_indicators, parse_metrics, parse_trade_sheet


class HeadlineParserTests(unittest.TestCase):
    def test_homepage_key_indicators_parse_newer_month(self):
        homepage = """
        <h2>Key indicators</h2>
        <p>Growth rate of some key indicators in September 2026 compared to the same period last year</p>
        <table>
          <tr><td>Index of Industrial Production</td><td>16.7%</td></tr>
          <tr><td>Retail sales of goods and services</td><td>14.1%</td></tr>
        </table>
        <h2>The most visited</h2>
        """
        actual = parse_homepage_key_indicators(homepage)
        self.assertEqual(actual["industrial_production"]["value"], 16.7)
        self.assertEqual(actual["industrial_production"]["period"], "September 2026")
        self.assertEqual(actual["retail_sales"]["value"], 14.1)

    def test_monthly_report_indicators(self):
        release = {
            "archive": "monthly-report",
            "title": "Report socio-economic performance in August and 8 months of 2026",
            "url": "https://example.test/monthly",
        }
        text = (
            "Total disbursed FDI in Viet Nam "
            "in the eight months of 2026 was estimated at 17.25 billion USD "
            "(+12.0% YoY). Cumulatively, for the eight months of 2026, the IIP "
            "advanced by 11.9% over the corresponding period last year. "
            "The retail sales of goods and services for the eight months of 2026 "
            "were estimated at 5,235.5 trillion VND, a year-on-year shoot of 13.3%. "
            "Overall, the export turnover of goods in the eight months of 2026 "
            "obtained 374.84 billion USD (+22.4% YoY). Overall, the import turnover "
            "of goods in the eight months of 2026 attained 395.3 billion USD, "
            "a year-on-year surge of 35.3%. Exports and imports shot up 22.4% and "
            "35.3%, respectively."
        )
        actual = parse_metrics(release, text)
        self.assertEqual(actual["fdi"], {"value": 17.25, "yoy": 12.0, "period": "January–August 2026"})
        self.assertEqual(actual["industrial_production"]["value"], 11.9)
        self.assertEqual(actual["retail_sales"]["value"], 13.3)
        self.assertEqual(actual["exports"]["value"], 374.84)
        self.assertEqual(actual["exports"]["yoy"], 22.4)
        self.assertEqual(actual["imports"]["value"], 395.3)
        self.assertEqual(actual["imports"]["yoy"], 35.3)
        quarterly = {
            **release,
            "title": "Report socio-economic performance in second quarter and the first half of 2026",
        }
        quarter_metrics = parse_metrics(
            quarterly,
            "Gross Domestic Product (GDP) in the second quarter of 2026 recorded robust expansion, rising by an estimated 8.39% year-on-year. The unemployment rate at working age in Q2 2026 was 2.23%.",
        )
        self.assertEqual(quarter_metrics["gdp_growth"]["value"], 8.39)
        self.assertEqual(quarter_metrics["unemployment"]["value"], 2.23)

    def test_cpi_is_rebased_to_current_index_display(self):
        release = {
            "archive": "cpi",
            "title": "Consumer Price Index in September of 2026",
            "url": "https://example.test/cpi",
        }
        actual = parse_metrics(release, "The Consumer Price Index (CPI) in September increased by 5.08% year on year.")
        self.assertEqual(actual["cpi"]["value"], 105.08)
        self.assertEqual(actual["cpi"]["period"], "September 2026")

    def test_trade_total_uses_latest_cumulative_thousand_usd_value(self):
        rows = [
            ["Preliminary Exports of goods In 2026"],
            [],
            ["Goods", "January", "", "February", "", "August", "", "8 months"],
            ["", "Quantity", "Value", "Quantity", "Value", "Quantity", "Value", "Quantity", "Value"],
            ["Total", "1", "100", "2", "200", "3", "4", "", "374836705.918"],
        ]
        actual = parse_trade_sheet("exports", rows, "Exports and imports value by months of 2026")
        self.assertAlmostEqual(actual["value"], 374.836705918)
        self.assertEqual(actual["period"], "January–August 2026 · preliminary")

    def test_trade_workbook_conversion_uses_temp_path_inside_repository(self):
        release = {"url": "https://example.test/trade", "title": "Exports and imports value by months of 2026"}
        links = ["https://example.test/E01_2026.xlsx"]
        rows = [["Preliminary Exports of goods In 2026"], ["Total", "374836705.918"]]
        observed_paths = []

        def fake_convert(_data, _url, destination):
            observed_paths.append(Path(destination))
            return [{"rows_data": rows}]

        module = SimpleNamespace(convert=fake_convert, release_links=lambda _url: (links, []))
        with patch.dict("sys.modules", {"update_monthly_data": module}), \
                patch.object(update_latest_headlines, "fetch", return_value=b"workbook"):
            result = update_latest_headlines.parse_trade_workbooks(release)

        self.assertTrue(observed_paths[0].is_relative_to(update_latest_headlines.ROOT))
        self.assertIn("exports", result)


if __name__ == "__main__":
    unittest.main()
