from io import BytesIO

from validation import validate_and_clean_csv


def test_valid_dataset_is_cleaned():
    raw = b"Date,Item_Name,Category,Amount_INR\n2026-09-01, Rice , Grocery ,1200\n"
    result = validate_and_clean_csv(BytesIO(raw))
    assert result.valid
    assert result.valid_rows == 1
    assert result.cleaned_data.iloc[0]["Category"] == "Grocery"


def test_missing_column_is_reported():
    result = validate_and_clean_csv(b"Date,Item_Name,Category\n2026-09-01,Rice,Grocery\n")
    assert not result.valid
    assert "Amount_INR" in result.errors[0]


def test_bad_dates_negative_and_blank_values_are_excluded():
    raw = b"Date,Item_Name,Category,Amount_INR\nnot-a-date,Rice,Grocery,10\n2026-09-01,,Grocery,20\n2026-09-02,Milk,Dairy,-5\n2026-09-03,Tea,Beverages,30\n"
    result = validate_and_clean_csv(raw)
    assert result.valid
    assert result.valid_rows == 1
    assert result.invalid_rows == 3


def test_empty_file_is_safe():
    result = validate_and_clean_csv(b"")
    assert not result.valid
    assert result.errors