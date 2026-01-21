import datetime
from typing import Union

DATE_FORMAT = "%Y-%m-%d"

def get_week_start(date_str: str) -> str:
    """
    Calcula a data de início da semana (Segunda-feira) para uma data fornecida.
    A semana começa na Segunda-feira (weekday 0) e termina no Domingo (weekday 6).
    """
    date_obj = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    # weekday() retorna 0 para Segunda e 6 para Domingo.
    # Subtrai o número de dias passados desde a Segunda-feira.
    start_of_week = date_obj - datetime.timedelta(days=date_obj.weekday())
    return start_of_week.strftime(DATE_FORMAT)

def get_week_end(date_str: str) -> str:
    """
    Calcula a data de fim da semana (Domingo) para uma data fornecida.
    """
    date_obj = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    # Adiciona o número de dias restantes até o Domingo (6 - weekday()).
    end_of_week = date_obj + datetime.timedelta(days=6 - date_obj.weekday())
    return end_of_week.strftime(DATE_FORMAT)

def get_current_week_range(today: Union[str, None] = None) -> tuple[str, str]:
    """
    Retorna o intervalo de datas (Segunda-feira, Domingo) da semana atual.
    
    Args:
        today: Data de referência (YYYY-MM-DD). Se None, usa a data atual do sistema.
        
    Returns:
        Tupla (week_start, week_end).
    """
    if today is None:
        today = datetime.datetime.now().strftime(DATE_FORMAT)
        
    week_start = get_week_start(today)
    week_end = get_week_end(today)
    
    return week_start, week_end

def is_date_in_week(date_str: str, week_start_str: str) -> bool:
    """
    Verifica se uma data está dentro da semana que começa em week_start_str.
    """
    date_obj = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    week_start_obj = datetime.datetime.strptime(week_start_str, DATE_FORMAT).date()
    week_end_obj = week_start_obj + datetime.timedelta(days=6)

    return week_start_obj <= date_obj <= week_end_obj

# Exemplo de uso:
if __name__ == '__main__':
    today = datetime.date.today().strftime(DATE_FORMAT)
    print(f"Data de hoje: {today}")
    
    # Exemplo para uma data específica (Quarta-feira)
    test_date = "2026-01-21" # Quarta-feira
    start = get_week_start(test_date)
    end = get_week_end(test_date)
    
    print(f"Data de teste: {test_date}")
    print(f"Início da semana (Segunda): {start}") # Deve ser 2026-01-19
    print(f"Fim da semana (Domingo): {end}")     # Deve ser 2026-01-25
    
    # Teste de is_date_in_week
    print(f"2026-01-20 está na semana? {is_date_in_week('2026-01-20', start)}") # True
    print(f"2026-01-26 está na semana? {is_date_in_week('2026-01-26', start)}") # False (próxima semana)
    print(f"2026-01-18 está na semana? {is_date_in_week('2026-01-18', start)}") # False (semana anterior)
