import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Указываем путь к файлу credentials.json
CREDENTIALS_FILE = 'H:/RoboJulia/credentials.json'

# Название таблицы и листа
SPREADSHEET_NAME = 'EnergyBD'
SHEET_NAME = 'прайс'

# Авторизация
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# Открываем таблицу и лист
spreadsheet = client.open(SPREADSHEET_NAME)
sheet = spreadsheet.worksheet(SHEET_NAME)

# Читаем все данные
data = sheet.get_all_values()

# Выводим данные в консоль
for row in data:
    print(row)

input("Нажмите Enter, чтобы закрыть окно...")
