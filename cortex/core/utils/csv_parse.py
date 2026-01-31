from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path
import csv
from cortex.core.types.telescope import TSModel


class CSVColumnType(str, Enum):
    """DuckDB-compatible data types for CSV columns"""
    VARCHAR = "VARCHAR"
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    DOUBLE = "DOUBLE"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"


class CSVColumnMapping(TSModel):
    """Type mapping for a single CSV column"""
    column_name: str
    inferred_type: CSVColumnType
    nullable: bool = True
    sample_values: Optional[List[str]] = None  # For debugging
    date_format: Optional[str] = None  # Detected date/timestamp format (e.g., "%Y-%m-%d")


class CSVTypeInference(TSModel):
    """Complete type inference result for a CSV file"""
    filename: str
    column_mappings: List[CSVColumnMapping]
    total_rows_sampled: int

    def to_duckdb_types_dict(self) -> Dict[str, str]:
        """Convert to DuckDB columns parameter format"""
        return {
            col.column_name: col.inferred_type.value
            for col in self.column_mappings
        }


class CSVParserUtil:
    """Utility for inferring CSV column types"""

    @staticmethod
    def infer_types(csv_path: str | Path, sample_size: int = 2) -> CSVTypeInference:
        """
        Infer column types from CSV file by sampling rows

        Args:
            csv_path: Path to CSV file
            sample_size: Number of rows to sample from each section (start/middle/end)

        Returns:
            CSVTypeInference with detected column types
        """
        csv_path = Path(csv_path)

        # Read header and sample rows
        header, sampled_rows = CSVParserUtil._sample_rows(csv_path, sample_size)

        # Infer type for each column
        column_mappings = []
        for col_idx, col_name in enumerate(header):
            # Get all values for this column from sampled rows
            col_values = [row[col_idx] for row in sampled_rows if col_idx < len(row)]

            inferred_type, date_format = CSVParserUtil._infer_column_type(col_values)

            column_mappings.append(CSVColumnMapping(
                column_name=col_name,
                inferred_type=inferred_type,
                date_format=date_format,
                sample_values=col_values[:3]  # Keep first 3 for debugging
            ))

        return CSVTypeInference(
            filename=csv_path.name,
            column_mappings=column_mappings,
            total_rows_sampled=len(sampled_rows)
        )

    @staticmethod
    def _sample_rows(csv_path: Path, sample_size: int) -> tuple[List[str], List[List[str]]]:
        """
        Sample rows from start, middle, and end of CSV

        Args:
            csv_path: Path to CSV file
            sample_size: Number of rows from each section

        Returns:
            Tuple of (header, sampled_rows)
        """
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Keep original column names to match CSV exactly

            all_rows = list(reader)
            total_rows = len(all_rows)

            if total_rows == 0:
                return header, []

            # Calculate indices for start, middle, end
            start_rows = all_rows[:sample_size]

            if total_rows > sample_size * 2:
                middle_start = (total_rows // 2) - (sample_size // 2)
                middle_rows = all_rows[middle_start:middle_start + sample_size]

                end_rows = all_rows[-sample_size:]
            else:
                # File too small, just use what we have
                middle_rows = []
                end_rows = all_rows[sample_size:sample_size * 2] if total_rows > sample_size else []

            sampled_rows = start_rows + middle_rows + end_rows
            return header, sampled_rows

    @staticmethod
    def _infer_column_type(values: List[str]) -> tuple[CSVColumnType, Optional[str]]:
        """
        Infer column type from sample values

        Type precedence order: BOOLEAN → DOUBLE → INTEGER → TIMESTAMP → DATE → VARCHAR

        Args:
            values: Sample values from the column

        Returns:
            Tuple of (inferred_type, date_format)
            - date_format is only set for DATE/TIMESTAMP types
        """
        if not values or all(v.strip() == '' for v in values):
            return CSVColumnType.VARCHAR, None

        # Filter out empty/null values for type checking
        non_empty_values = [v.strip() for v in values if v.strip()]

        if not non_empty_values:
            return CSVColumnType.VARCHAR, None

        # Try BOOLEAN first (true/false, yes/no, 1/0, t/f, y/n)
        if CSVParserUtil._is_boolean(non_empty_values):
            return CSVColumnType.BOOLEAN, None

        # Try DOUBLE (must check before INTEGER to catch decimals)
        if CSVParserUtil._is_double(non_empty_values):
            # Check if it's actually an integer (no decimal part)
            if CSVParserUtil._is_integer(non_empty_values):
                return CSVColumnType.INTEGER, None
            return CSVColumnType.DOUBLE, None

        # Try TIMESTAMP (with time component)
        timestamp_format = CSVParserUtil._detect_timestamp_format(non_empty_values)
        if timestamp_format:
            return CSVColumnType.TIMESTAMP, timestamp_format

        # Try DATE (without time component)
        date_format = CSVParserUtil._detect_date_format(non_empty_values)
        if date_format:
            return CSVColumnType.DATE, date_format

        # Default to VARCHAR
        return CSVColumnType.VARCHAR, None

    @staticmethod
    def _is_boolean(values: List[str]) -> bool:
        """
        Check if values are boolean-like

        Note: Excludes numeric strings '0' and '1' to avoid confusion with integers.
        Only accepts explicit boolean strings like 'true', 'false', 'yes', 'no', etc.
        """
        # Exclude numeric 0/1 to avoid confusion with integers
        # Only accept explicit boolean text values
        bool_values = {'true', 'false', 'yes', 'no', 't', 'f', 'y', 'n'}
        unique_lower = {v.lower() for v in values}
        return unique_lower.issubset(bool_values) and len(unique_lower) <= 2

    @staticmethod
    def _is_double(values: List[str]) -> bool:
        """Check if values are numeric (float)"""
        try:
            for v in values:
                float(v)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_integer(values: List[str]) -> bool:
        """Check if numeric values are integers (no decimal part)"""
        try:
            for v in values:
                num = float(v)
                if num != int(num):
                    return False
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _detect_date_format(values: List[str]) -> Optional[str]:
        """
        Check if values are dates (without time) and detect format

        Returns:
            Date format string (e.g., "%Y-%m-%d") or None if not a date
        """
        from dateutil import parser

        try:
            parsed_dates = []
            for v in values:
                parsed = parser.parse(v, fuzzy=False)
                # Check if it has time component (hours, minutes, seconds)
                if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0:
                    return None
                parsed_dates.append(parsed)

            # All values parsed successfully as dates (no time)
            # Try to infer format from the first value
            format_str = CSVParserUtil._infer_date_format(values[0], parsed_dates[0])
            # If we can't determine the format, treat as VARCHAR
            if format_str is None:
                return None
            return format_str

        except (ValueError, TypeError, parser.ParserError):
            return None

    @staticmethod
    def _detect_timestamp_format(values: List[str]) -> Optional[str]:
        """
        Check if values are timestamps (with time) and detect format

        Returns:
            Timestamp format string (e.g., "%Y-%m-%d %H:%M:%S") or None if not a timestamp
        """
        from dateutil import parser

        try:
            parsed_dates = []
            has_time_component = False
            for v in values:
                parsed = parser.parse(v, fuzzy=False)
                # Check if any value has a time component (hours, minutes, seconds, microseconds)
                if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0 or parsed.microsecond != 0:
                    has_time_component = True
                parsed_dates.append(parsed)

            # Only consider it a timestamp if at least one value has a time component
            if not has_time_component:
                return None

            # All values parsed successfully and have time components
            # Try to infer format from the first value
            format_str = CSVParserUtil._infer_datetime_format(values[0], parsed_dates[0])
            return format_str

        except (ValueError, TypeError, parser.ParserError):
            return None

    @staticmethod
    def _infer_date_format(date_str: str, parsed_date) -> str:
        """
        Infer the date format string from a sample date

        Common patterns:
        - YYYY-MM-DD → %Y-%m-%d
        - MM/DD/YYYY → %m/%d/%Y
        - DD/MM/YYYY → %d/%m/%Y
        - YYYY/MM/DD → %Y/%m/%d
        """
        # Common date formats to try
        common_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m-%d-%y",   # 04-30-22
            "%m/%d/%y",   # 04/30/22
            "%d-%m-%y",   # 30-04-22
            "%d/%m/%y",   # 30/04/22
            "%Y%m%d",
            "%b %d, %Y",  # Jan 15, 2023
            "%B %d, %Y",  # January 15, 2023
            "%d %b %Y",   # 15 Jan 2023
            "%d %B %Y",   # 15 January 2023
        ]

        from datetime import datetime
        for fmt in common_formats:
            try:
                if datetime.strptime(date_str, fmt) == parsed_date.replace(tzinfo=None):
                    return fmt
            except ValueError:
                continue

        # Return None if no format matches
        return None

    @staticmethod
    def _infer_datetime_format(datetime_str: str, parsed_datetime) -> str:
        """
        Infer the datetime format string from a sample timestamp

        Common patterns:
        - YYYY-MM-DD HH:MM:SS → %Y-%m-%d %H:%M:%S
        - YYYY-MM-DDTHH:MM:SS → %Y-%m-%dT%H:%M:%S (ISO format)
        - MM/DD/YYYY HH:MM:SS → %m/%d/%Y %H:%M:%S
        """
        # Common datetime formats to try
        common_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%m/%d/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %H:%M",
        ]

        from datetime import datetime
        for fmt in common_formats:
            try:
                if datetime.strptime(datetime_str, fmt) == parsed_datetime.replace(tzinfo=None):
                    return fmt
            except ValueError:
                continue

        # Default fallback
        return "%Y-%m-%d %H:%M:%S"
