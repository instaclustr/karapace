from enum import Enum


class KnownDependencyLocation(Enum):
    ANY_LOCATION = "google/protobuf/any.proto"
    API_LOCATION = "google/protobuf/api.proto"
    DESCRIPTOR_LOCATION = "google/protobuf/descriptor.proto"
    DURATION_LOCATION = "google/protobuf/duration.proto"
    EMPTY_LOCATION = "google/protobuf/empty.proto"
    FIELD_MASK_LOCATION = "google/protobuf/field_mask.proto"
    SOURCE_CONTEXT_LOCATION = "google/protobuf/source_context.proto"
    STRUCT_LOCATION = "google/protobuf/struct.proto"
    TIMESTAMP_LOCATION = "google/protobuf/timestamp.proto"
    TYPE_LOCATION = "google/protobuf/type.proto"
    WRAPPER_LOCATION = "google/protobuf/wrappers.proto"
    CALENDAR_PERIOD_LOCATION = "google/type/calendar_period.proto"
    COLOR_LOCATION = "google/type/color.proto"
    DATE_LOCATION = "google/type/date.proto"
    DATETIME_LOCATION = "google/type/datetime.proto"
    DAY_OF_WEEK_LOCATION = "google/type/dayofweek.proto"
    DECIMAL_LOCATION = "google/type/decimal.proto"
    EXPR_LOCATION = "google/type/expr.proto"
    FRACTION_LOCATION = "google/type/fraction.proto"
    INTERVAL_LOCATION = "google/type/interval.proto"
    LATLNG_LOCATION = "google/type/latlng.proto"
    MONEY_LOCATION = "google/type/money.proto"
    MONTH_LOCATION = "google/type/month.proto"
    PHONE_NUMBER_LOCATION = "google/type/phone_number.proto"
    POSTAL_ADDRESS_LOCATION = "google/type/postal_address.proto"
    QUATERNION_LOCATION = "google/type/quaternion.proto"
    TIME_OF_DAY_LOCATION = "google/type/timeofday.proto"


class KnownDependency(Enum):
    pass
