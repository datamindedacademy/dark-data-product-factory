{#
  Grain test: the combination of `combination_of_columns` must be unique.
  Usage (model level):
    data_tests:
      - unique_combination_of_columns:
          arguments:
            combination_of_columns: [month, category]
#}
{% test unique_combination_of_columns(model, combination_of_columns) %}
select {{ combination_of_columns | join(', ') }}, count(*) as n_rows
from {{ model }}
group by {{ combination_of_columns | join(', ') }}
having count(*) > 1
{% endtest %}
