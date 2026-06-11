import asyncio
import io
import pandas as pd
from fastapi import UploadFile
from app.core.db_helper import db_helper
from app.modules.employee.service import EmployeeService
from app.modules.employee.repository import EmployeeRepository

async def test():
    data = [
        {
            "Last Name": "Toshmatov",
            "First Name": "Eshmat",
            "Sharif": "Toshmatovich",
            "Pasport": "AA1234567",
            "JSHIR": "12345678901234",
            "Stavka": "1.0",
            "Lavozim": "Dasturchi",
            "Bo'lim": "IT",
            "Ishdami": "Ha"
        },
        # 1. Row with invalid JSHIR (less than 14 digits)
        {
            "Last Name": "Olimov",
            "First Name": "Olim",
            "Sharif": "Olimovich",
            "Pasport": "AA9999999",
            "JSHIR": "123456",
            "Stavka": "1.0",
            "Lavozim": "Dasturchi",
            "Bo'lim": "IT",
            "Ishdami": "Ha"
        },
        # 2. Row with duplicate passport series (AA1234567 already belongs to Toshmatov)
        {
            "Last Name": "Karimov",
            "First Name": "Karim",
            "Sharif": "Karimovich",
            "Pasport": "AA1234567",
            "JSHIR": "98765432101234",
            "Stavka": "1.0",
            "Lavozim": "Dasturchi",
            "Bo'lim": "IT",
            "Ishdami": "Ha"
        }
    ]
    df = pd.DataFrame(data)
    
    excel_io = io.BytesIO()
    with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_io.seek(0)
    
    upload_file = UploadFile(
        file=excel_io,
        filename="test_employees.xlsx",
        headers={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    )
    
    async with db_helper.session_factory() as session:
        repo = EmployeeRepository(session)
        service = EmployeeService(repo)
        
        response = await service.upload_excel(upload_file)
        print("Success:", response.success)
        print("Imported count:", response.imported_count)
        print("Errors:")
        for err in response.errors:
            print(" -", err)

if __name__ == "__main__":
    asyncio.run(test())
