from feast import Entity
from feast.value_type import ValueType

candidate = Entity(name="candidate", join_keys=["CANDIDATE_ID"], value_type=ValueType.INT64)
job = Entity(name="job", join_keys=["JOB_ID"], value_type=ValueType.INT64)