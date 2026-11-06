{# Keep every model in the target schema (main). Raw data lives in schema `raw`. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ target.schema }}
{%- endmacro %}
