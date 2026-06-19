import json
from datetime import datetime, timezone, timedelta

import httpx

# UTC-3 (São Paulo, sem DST desde 2019)
BRAZIL_TZ = timezone(timedelta(hours=-3))

WMO_CODES = {
    0: "céu limpo",
    1: "principalmente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "névoa",
    48: "névoa com depósito de geada",
    51: "garoa fraca",
    53: "garoa moderada",
    55: "garoa forte",
    61: "chuva fraca",
    63: "chuva moderada",
    65: "chuva forte",
    71: "neve fraca",
    73: "neve moderada",
    75: "neve forte",
    80: "pancadas de chuva fraca",
    81: "pancadas de chuva moderada",
    82: "pancadas de chuva forte",
    95: "tempestade",
    96: "tempestade com granizo",
    99: "tempestade com granizo forte",
}

WEEKDAYS = [
    "segunda-feira", "terça-feira", "quarta-feira",
    "quinta-feira", "sexta-feira", "sábado", "domingo",
]


async def get_current_time() -> dict:
    now = datetime.now(BRAZIL_TZ)
    return {
        "data": now.strftime("%d/%m/%Y"),
        "hora": now.strftime("%H:%M"),
        "dia_da_semana": WEEKDAYS[now.weekday()],
    }


async def get_weather(city: str, date: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "pt", "format": "json"},
        )
        geo_data = geo.json()
        if not geo_data.get("results"):
            return {"erro": f"Cidade '{city}' não encontrada"}

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        params: dict = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "timezone": "America/Sao_Paulo",
            "forecast_days": 7,
        }
        if date:
            params["start_date"] = date
            params["end_date"] = date
            params["forecast_days"] = 16

        resp = await client.get("https://api.open-meteo.com/v1/forecast", params=params)

        if resp.status_code != 200:
            try:
                reason = resp.json().get("reason", "erro desconhecido")
            except Exception:
                reason = resp.text[:100]
            return {"erro": f"Open-Meteo retornou erro: {reason}. Previsões disponíveis para no máximo 16 dias no futuro."}

        daily = resp.json().get("daily", {})
        dates = daily.get("time", [])

        if not dates:
            return {"erro": "Nenhum dado disponível para essa data/cidade."}

        forecast = []
        for i, d in enumerate(dates):
            code = int(daily["weather_code"][i]) if daily.get("weather_code") else 0
            forecast.append({
                "data": d,
                "temp_max": f"{daily['temperature_2m_max'][i]}°C",
                "temp_min": f"{daily['temperature_2m_min'][i]}°C",
                "probabilidade_chuva": f"{daily['precipitation_probability_max'][i]}%",
                "condicao": WMO_CODES.get(code, f"código {code}"),
            })

        return {"cidade": loc["name"], "previsao": forecast}


TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
}

TOOLS_SCHEMA = [
    {
        "functionDeclarations": [
            {
                "name": "get_current_time",
                "description": "Retorna a data e hora atual no Brasil (fuso de São Paulo). Use quando precisar saber que horas são ou que dia é hoje.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_weather",
                "description": "Busca previsão do tempo real para uma cidade. Funciona para hoje e até 16 dias no futuro. Informe o nome da cidade e, opcionalmente, uma data específica.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Nome da cidade, ex: 'São Paulo', 'Rio de Janeiro', 'Tatuapé'",
                        },
                        "date": {
                            "type": "string",
                            "description": "Data no formato YYYY-MM-DD. Omitir para retornar os próximos 7 dias.",
                        },
                    },
                    "required": ["city"],
                },
            },
        ]
    }
]


async def execute_tool(name: str, args: dict) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return {"erro": f"Função '{name}' não existe"}
    try:
        return await func(**args)
    except Exception as e:
        return {"erro": str(e)}
