import sys
from sqlalchemy.orm import Session
from database import SessionLocal, TestConfigDB, TestParameterDB
from data import REFERENCE_DB

def add_cbc():
    db = SessionLocal()
    try:
        if db.query(TestConfigDB).filter(TestConfigDB.name == "CBC").first():
            print("CBC already exists.")
            return

        test_config = TestConfigDB(name="CBC", price=400.0)
        db.add(test_config)
        db.flush()

        cbc_params = REFERENCE_DB.get("CBC", [])
        for param in cbc_params:
            test_param = TestParameterDB(
                test_config_id=test_config.id,
                investigation=param["Investigation"],
                ref_min=param["Ref_Min"],
                ref_max=param["Ref_Max"],
                unit=param["Unit"],
                type=param.get("Type", "numeric")
            )
            db.add(test_param)
        db.commit()
        print("Successfully added CBC to the database.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_cbc()
