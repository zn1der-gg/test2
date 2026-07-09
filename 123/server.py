from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import requests_cache
import random

app = FastAPI()

# Разрешаем Telegram-приложению делать запросы к нашему серверу
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Кэшируем запросы к HLTV на 5 минут, чтобы сайт нас не заблокировал
requests_cache.install_cache('hltv_cache', expire_after=300)

def parse_hltv_matches():
    url = "https://www.hltv.org/matches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Находим блоки предстоящих и live матчей
        match_sections = soup.find_all("div", class_="upcomingMatch")
        parsed_matches = []
        
        for idx, match in enumerate(match_sections[:10]): # Берем первые 10 актуальных матчей
            team1_el = match.find("div", class_="team1")
            team2_el = match.find("div", class_="team2")
            event_el = match.find("div", class_="matchEventName")
            time_el = match.find("div", class_="matchTime")
            
            if team1_el and team2_el:
                t1_name = team1_el.text.strip()
                t2_name = team2_el.text.strip()
                event_name = event_el.text.strip() if event_el else "HLTV Tournament"
                match_time = "LIVE" if match.find("div", class_="matchLive") else (time_el.text.strip() if time_el else "Скоро")
                
                # Базовый алгоритм генерации коэффициентов на основе случайного распределения сил сил (симуляция БК)
                # В реальном API коэффициенты берутся готовыми, при парсинге HLTV мы их рассчитываем математически
                seed = random.uniform(1.3, 2.8)
                odd1 = round(seed, 2)
                odd2 = round(4.0 / seed, 2) # Обратная пропорция для маржи
                
                parsed_matches.append({
                    "id": idx + 1,
                    "team1": t1_name,
                    "team2": t2_name,
                    "event": event_name,
                    "time": match_time,
                    "odd1": odd1,
                    "odd2": odd2
                })
        return parsed_matches
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return []

@app.get("/api/matches")
def get_matches():
    """Эндпоинт, который будет вызывать твой фронтенд"""
    matches = parse_hltv_matches()
    if not matches:
        # Если HLTV временно заблокировал запрос, отдаем дефолтные матчи
        return [
            {"id": 1, "team1": "Natus Vincere", "team2": "FaZe Clan", "event": "PGL Major", "time": "LIVE", "odd1": 1.65, "odd2": 2.25},
            {"id": 2, "team1": "Team Vitality", "team2": "G2 Esports", "event": "IEM Katowice", "time": "19:30", "odd1": 1.85, "odd2": 1.95}
        ]
    return matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)