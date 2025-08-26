from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError
from cortex.core.types.dashboards import AxisDataType, ValueSelectionMode, NumberFormat


class SingleValueMapping(VisualizationMapping):
    """Mapping configuration for single value visualizations."""
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for single value visualization."""
        # Single value uses x_axis as the value field
        if not self.data_mapping.x_axis:
            raise MappingValidationError("x_axis", "Single value visualization requires an x_axis mapping")
        # Validate x exists
        self.data_mapping.x_axis.validate_against_result(result_columns)
    
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for single value visualization."""
        return ["x_axis"]
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data for single value display."""
        if not metric_result:
            return {"value": None, "formatted_value": "No data"}
        
        value_field = self.data_mapping.x_axis.field
        
        # For single value, we typically want the first row or aggregated value
        value = self._select_value(metric_result, value_field)
        # If selection mode is concat, allow string outputs; otherwise ensure numeric
        sel_mode = getattr(self, 'selection_mode', ValueSelectionMode.FIRST)
        if sel_mode != ValueSelectionMode.CONCAT:
            try:
                if isinstance(value, str):
                    value = float(value)
            except Exception:
                raise MappingValidationError("x_axis", f"Single value requires numeric data. Column '{value_field}' contains non-numeric value: {value}")
        
        # Apply formatting if configured
        formatted_value = self._format_value(value)
        
        return {
            "value": value,
            "formatted_value": formatted_value,
            "field_name": value_field,
            "field_label": (self.data_mapping.x_axis.label or value_field)
        }
    
    def _format_value(self, value: Any) -> str:
        """Format the value according to field formatting configuration."""
        if value is None:
            return (self.data_mapping.x_axis.format.show_null_as if self.data_mapping.x_axis and self.data_mapping.x_axis.format else "N/A")

        if not (self.data_mapping.x_axis and self.data_mapping.x_axis.format):
            return str(value)

        fmt = self.data_mapping.x_axis.format
        numeric = value if isinstance(value, (int, float)) else None
        try:
            if numeric is None:
                numeric = float(value)
        except Exception:
            numeric = None

        formatted = str(value)

        # Respect number_format if provided
        if numeric is not None:
            nf = getattr(fmt, 'number_format', None)
            if isinstance(nf, NumberFormat):
                nf_val = nf.value
            else:
                nf_val = (nf or '').lower() if isinstance(nf, str) else None

            if nf_val == 'integer':
                formatted = f"{round(numeric):,}"
            elif nf_val == 'decimal':
                dp = fmt.decimal_places if fmt.decimal_places is not None else 2
                formatted = f"{numeric:,.{dp}f}"
            elif nf_val == 'percentage':
                formatted = f"{numeric * 100:,.1f}%"
            elif nf_val == 'currency':
                # No currency code available here; leave as locale-neutral
                dp = fmt.decimal_places if fmt.decimal_places is not None else 2
                formatted = f"{numeric:,.{dp}f}"
            elif nf_val == 'abbreviated':
                abs_val = abs(numeric)
                if abs_val >= 1e9:
                    formatted = f"{numeric/1e9:.1f}B"
                elif abs_val >= 1e6:
                    formatted = f"{numeric/1e6:.1f}M"
                elif abs_val >= 1e3:
                    formatted = f"{numeric/1e3:.1f}K"
                else:
                    formatted = f"{numeric}"
            elif nf_val == 'scientific':
                formatted = f"{numeric:.2e}"
            else:
                # default behavior with optional decimal places
                if fmt.decimal_places is not None:
                    formatted = f"{numeric:,.{fmt.decimal_places}f}"
                else:
                    formatted = f"{numeric}"

        # Apply prefix and suffix
        if fmt.prefix:
            formatted = f"{fmt.prefix}{formatted}"
        if fmt.suffix:
            formatted = f"{formatted}{fmt.suffix}"

        return formatted

    def _select_value(self, rows: List[Dict[str, Any]], field: str) -> Any:
        """Select a value from multiple rows using selection config if present."""
        if not rows:
            return None
        mode: ValueSelectionMode = ValueSelectionMode.FIRST
        cfg: Dict[str, Any] = {}
        # Attempt to read selection from visualization config if attached via mapping factory path
        try:
            # MappingFactory passes full viz config to router; for single value we can’t access it directly here.
            # Read from data_mapping.x_axis.format.metadata if present (lightweight hook)
            pass
        except Exception:
            pass

        # Fallback: inspect TSModel-backed viz config if attached on instance
        sel_mode = getattr(self, 'selection_mode', None)
        sel_cfg = getattr(self, 'selection_config', None)
        if isinstance(sel_mode, ValueSelectionMode):
            mode = sel_mode
        if isinstance(sel_cfg, dict):
            cfg = sel_cfg

        if mode == ValueSelectionMode.FIRST:
            return rows[0].get(field)
        if mode == ValueSelectionMode.LAST:
            return rows[-1].get(field)
        if mode == ValueSelectionMode.NTH:
            n = int(cfg.get('n', 1))
            idx = max(0, min(len(rows)-1, n-1))
            return rows[idx].get(field)
        if mode == ValueSelectionMode.CONCAT:
            delim = cfg.get('delimiter', ',')
            return delim.join([str(r.get(field)) for r in rows if r.get(field) is not None])
        if mode == ValueSelectionMode.MIN:
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            return min(values) if values else None
        if mode == ValueSelectionMode.MAX:
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            return max(values) if values else None
        if mode in (ValueSelectionMode.MEAN, ValueSelectionMode.MEDIAN, ValueSelectionMode.MODE):
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            if not values:
                return None
            if mode == ValueSelectionMode.MEAN:
                return sum(values)/len(values)
            if mode == ValueSelectionMode.MEDIAN:
                s = sorted(values)
                m = len(s)//2
                return (s[m] if len(s)%2==1 else (s[m-1]+s[m])/2)
            if mode == ValueSelectionMode.MODE:
                try:
                    from statistics import mode as stats_mode
                    return stats_mode(values)
                except Exception:
                    # fallback to mean if multimodal
                    return sum(values)/len(values)
        if mode == ValueSelectionMode.AGGREGATE:
            how = (cfg.get('aggregate_by') or 'sum').lower()
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            if not values:
                return None
            if how == 'sum':
                return sum(values)
            if how in ('avg', 'mean'):
                return sum(values)/len(values)
            if how == 'median':
                s = sorted(values)
                m = len(s)//2
                return (s[m] if len(s)%2==1 else (s[m-1]+s[m])/2)
            if how == 'min':
                return min(values)
            if how == 'max':
                return max(values)
            return sum(values)
        return rows[0].get(field)
