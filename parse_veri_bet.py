from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass
import re
import json

@dataclass
class Item:
    sport_league: str = ''     # sport as we classify it, e.g. baseball, basketball, football
    event_date_utc: str = ''   # date of the event, in UTC, ISO format
    team1: str = ''            # team 1 name
    team2: str = ''            # team 2 name
    pitcher: str = ''          # optional, pitcher for baseball
    period: str = ''           # full time, 1st half, 1st quarter, and so on
    line_type: str = ''        # whatever the site reports as the line type, e.g., moneyline, spread, over/under
    price: str = ''            # price site reports, e.g., '-133' or '+105'
    side: str = ''             # side of the bet for over/under, e.g., 'over', 'under'
    team: str = ''             # team name; for over/under bets, this will be either the team name or 'total'
    spread: float = 0.0        # for handicap and over/under bets, e.g., -1.5, +2.5

def scraped_data(row, line_type, sport_league="NFL"):
    item = Item()
    item.team1 = row.find_element(By.XPATH, "//tr[2]/td[1]/table/tbody/tr/td/table/tbody/tr/td[1]/a/span").text.strip()
    item.team2 = row.find_element(By.XPATH, "//tr[3]/td[1]/table/tbody/tr/td/table/tbody/tr/td[1]/a/span").text.strip()
    item.sport_league = sport_league
    item.event_date_utc = row.find_element(By.XPATH, "//tr[4]/td[1]/table/tbody/tr/td/span[2]").text.strip()
    item.period = row.find_element(By.XPATH, "//tr[1]/td[1]/span").text.strip()

    if line_type == "moneyline":
        for i in range(2, 4):
            team_item = Item()
            team_item.team1 = item.team1
            team_item.team2 = item.team2
            team_item.line_type = line_type
            team_item.event_date_utc = item.event_date_utc
            team_item.period = item.period
            team_item.price = row.find_element(By.XPATH, f"//tr[{i}]/td[2]/table/tbody/tr/td/span").text.strip()
            
            if i == 2:
                team_item.side = item.team1
                team_item.team = item.team1
            else:
                team_item.side = item.team2
                team_item.team = item.team2

            moneyline_bets.append(team_item)

    if line_type == "spread":
        for i in range (2, 4):
            team_item = Item()
            team_item.team1 = item.team1
            team_item.team2 = item.team2
            team_item.line_type = line_type
            team_item.event_date_utc = item.event_date_utc
            team_item.period = item.period
            spread_text1 = row.find_element(By.XPATH, "//tr[2]/td[3]/table/tbody/tr/td/span").text.strip()
            spread_text2_elements = row.find_elements(By.XPATH, "//tr[3]/td[3]/table/tbody/tr/td/span")
            spread_parts1 = re.sub(r'[()]', '', spread_text1)
            values1 = spread_parts1.split('\n', 1)

            if i == 2:
                team_item.spread = values1[0]
                team_item.price = values1[1]
                team_item.side = item.team1
                team_item.team = item.team1

            else:
                spread_text2_elements = row.find_elements(By.XPATH, "//tr[3]/td[3]/table/tbody/tr/td/span")
                spread_text2 = spread_text2_elements[0].text.strip()
                spread_parts2 = re.sub(r'[()]', '', spread_text2)
                values2 = spread_parts2.split('\n', 1)

                team_item.spread = values2[0]
                team_item.price = values2[1]

                team_item.side = item.team2
                team_item.team = item.team2

            spread_bets.append(team_item)

    if line_type == "over/under":
        for i in range(2, 4):
            team_item = Item()
            team_item.sport_league = sport_league
            team_item.team1 = item.team1
            team_item.team2 = item.team2
            team_item.line_type = line_type
            team_item.event_date_utc = item.event_date_utc
            team_item.period = item.period

            price_raw = row.find_element(By.XPATH, "//tr[2]/td[4]/table/tbody/tr/td/span").text.strip()
            price_raw2 = row.find_element(By.XPATH, "//tr[3]/td[4]/table/tbody/tr/td/span").text.strip()

            match = re.search(r'\d+', price_raw)
            spread_result = match.group()

            match1 = re.search(r'\(([-+]?\d+)\)', price_raw)
            value1 = match1.group(1)

            match2 = re.search(r'\(([-+]?\d+)\)', price_raw2)
            value2 = match2.group(1)
            team_item.team = "total"
            team_item.spread = spread_result

            if i == 2:
                team_item.side = "over"
                team_item.price = value1
            else:
                team_item.side = "under"
                team_item.price = value2

            over_under_bets.append(team_item)
            
    return item

url = "https://veri.bet/simulator"

driver = webdriver.Chrome()
driver.get(url)

button_element = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.btn-lg')
button_element.click()

wait = WebDriverWait(driver, 30) # adjust conform your needs
element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "col col-md")]//table/tbody')))

moneyline_bets = []
spread_bets = []
over_under_bets = []

bet_data = []


for i in range(1, 5):
    row = element.find_element(By.XPATH, f'.//tr[{i}]')
    scraped_data(row, "moneyline")
    scraped_data(row, "spread")
    scraped_data(row, "over/under")

bet_data = moneyline_bets[:2] + spread_bets[:2] + over_under_bets[:2]
bet_data_dicts = [item.__dict__ for item in bet_data]
driver.quit()
print(json.dumps(bet_data_dicts, indent=2))
