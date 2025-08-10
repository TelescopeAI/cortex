# AI Agent Assistants

## Overview

This module contains AI-powered assistants built using LangGraph's React agent framework. The assistants leverage Cortex's semantic layer to provide intelligent analytics capabilities including schema analysis, metric suggestion, and automated insights generation.

## Core Architecture

### LangGraph React Agent Framework
- **Agent Type**: `create_react_agent` from LangGraph for rapid development
- **Tool-Based Design**: Modular tools that the agent can orchestrate
- **Pydantic Models**: All components inherit from `TSModel` for consistency
- **Integration**: Deep integration with existing Cortex semantic layer

### Primary Assistant: Semantic Analysis Agent

The main assistant (`SemanticAnalysisAgent`) provides four core capabilities through specialized tools:

1. **Schema Analysis**: Analyze database schemas and suggest potential metrics
2. **Metric Creation**: Generate semantic metric definitions with business context
3. **Metric Execution**: Execute metrics with context and provide intelligent analysis
4. **Pattern Recognition**: Identify data patterns that could become valuable metrics

## Tool Specifications

### SchemaAnalysisTool
- Analyzes database schemas to understand structure and relationships
- Suggests potential measures (numeric columns) and dimensions (categorical columns)
- Identifies aggregation opportunities and join possibilities
- Generates schema summaries with metric recommendations

### MetricCreationTool
- Creates `SemanticMetric` instances from natural language descriptions
- Validates metric definitions against available schema
- Suggests complementary metrics and variations
- Provides reasoning for metric design decisions

### MetricExecutionTool
- Executes metrics using existing `QueryExecutor` infrastructure
- Analyzes results for patterns, anomalies, and trends
- Provides business reasoning about results
- Suggests follow-up questions and drill-down opportunities

### PatternRecognitionTool
- Identifies interesting patterns in data for metric creation
- Analyzes query logs for common usage patterns
- Detects data quality issues requiring monitoring
- Suggests KPIs based on business domain analysis

## Integration with Cortex

### Leveraging Existing Infrastructure
- **Query Execution**: Uses existing `QueryExecutor` for metric execution
- **Semantic Layer**: Creates and validates `SemanticMetric` instances
- **Context Management**: Leverages `Consumer` properties and `MetricContext`
- **Data Sources**: Integrates with existing data source connectors
- **Security**: Applies existing RBAC and environment isolation

### Workflow Example
```
User: "Analyze the sales database and suggest some metrics"
↓
Agent orchestrates tools:
1. SchemaAnalysisTool → Discovers tables, columns, relationships
2. MetricCreationTool → Creates revenue, growth, and performance metrics
3. MetricExecutionTool → Executes sample metric with analysis
4. PatternRecognitionTool → Identifies seasonal patterns
↓
Agent provides comprehensive analysis with actionable insights
```

## Implementation Status

### Current Phase: Core Tools Development
- [ ] Schema analysis tool implementation
- [ ] Metric creation tool with validation
- [ ] LangGraph React Agent setup
- [ ] Basic Pydantic model definitions
- [ ] Integration with existing Cortex components

### Upcoming Phases
- **Week 2**: Metric execution and analysis capabilities
- **Week 3**: Advanced pattern recognition and business insights
- **Week 4**: Production readiness and optimization

## Usage Examples

### Schema Analysis
```python
agent = SemanticAnalysisAgent()
result = await agent.analyze_schema(
    data_source_id=uuid4(),
    include_samples=True
)
# Returns schema analysis with metric suggestions
```

### Metric Creation and Execution
```python
result = await agent.create_and_execute_metric(
    description="Monthly revenue by product category",
    data_source_id=uuid4(),
    context_id="consumer_12345"
)
# Returns created metric, execution results, and insights
```

### Pattern Analysis
```python
patterns = await agent.identify_patterns(
    data_source_id=uuid4(),
    analysis_type="business_kpis"
)
# Returns identified patterns and suggested metrics
```

## Technical Notes

### Pydantic Model Hierarchy
All models inherit from `TSModel` maintaining consistency with Cortex patterns:
- `SchemaAnalysisRequest/Result`
- `MetricCreationRequest/Result` 
- `MetricExecutionRequest/Result`
- `PatternAnalysisRequest/Result`

### Error Handling
- Comprehensive validation using Pydantic models
- Graceful degradation for LLM failures
- Integration with existing Cortex error handling patterns

### Performance Considerations
- Async execution for all tool operations
- Caching of schema analysis results
- Efficient integration with existing query execution pipeline

## Development Guidelines

1. **Inherit from TSModel**: All new models must inherit from `TSModel`
2. **Tool Modularity**: Each tool should be independently testable
3. **Integration First**: Leverage existing Cortex infrastructure
4. **Validation**: Comprehensive input/output validation
5. **Documentation**: Clear docstrings and usage examples

## Future Enhancements

- Multi-agent orchestration for complex analytical workflows
- Real-time learning from user interactions
- Domain-specific knowledge integration
- Advanced visualization recommendations
- Collaborative analytics features