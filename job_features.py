from datetime import timedelta
from feast import FeatureView, Field
from feast.types import String
from entities import job
from feast import FileSource

job_source = FileSource(
    name="job_source",
    path="job_data.parquet",
    timestamp_field="event_timestamp"
)

job_fv = FeatureView(
    name="job_features",
    entities=[job],
    ttl=timedelta(days=365),
    schema=[
        Field(name="REQUIRED_SKILL_LIST", dtype=String),
        Field(name="LOCATION", dtype=String),
    ],
    source=job_source,
)