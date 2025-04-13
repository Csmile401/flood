import requests
from bs4 import BeautifulSoup

url = "https://ihydro.sarawak.gov.my/iHydro/en/datatable/waterlevel/hourly-waterlevel.jsp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 示例：提取表格数据
table = soup.find("table")  # 根据实际的 HTML 结构调整选择器
rows = table.find_all("tr")

for row in rows:
    cells = row.find_all("td")
    data = [cell.get_text(strip=True) for cell in cells]
    print(data)
