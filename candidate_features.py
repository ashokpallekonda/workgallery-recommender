from datetime import timedelta
from feast import FeatureView, Field
from feast.types import String, Int32
from entities import candidate
from feast import FileSource

candidate_source = FileSource(
    name="candidate_source",
    path="candidate_data.parquet",
    timestamp_field="event_timestamp"
)

candidate_fv = FeatureView(
    name="candidate_features",
    entities=[candidate],
    ttl=timedelta(days=365),
    schema=[
        Field(name="SKILL_LIST", dtype=String),
        Field(name="EXPERIENCE_YEARS", dtype=Int32),
        Field(name="LOCATION", dtype=String),
    ],
    source=candidate_source,
)