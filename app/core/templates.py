from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
import os

templates = Jinja2Templates(directory="app/templates")

@pass_context
def get_csrf_token(context):
    request = context.get("request")
    if request:
        cookie_token = request.cookies.get("csrftoken")
        if cookie_token:
            return cookie_token
        return request.scope.get("csrf_token") or ""
    return ""

def format_especialidade(esp_string: str):
    if not esp_string:
        return []
    mapping = {
        'MOTORES': 'MOT', 'MOT': 'MOT',
        'CÉLULA': 'CEL', 'CEL': 'CEL',
        'HIDRÁULICA': 'HID', 'HID': 'HID',
        'ELETRÔNICA': 'ELT', 'ELT': 'ELT',
        'ELÉTRICA': 'ELE', 'ELE': 'ELE',
        'PINTURA': 'EST', 'ESTRUTURA': 'EST', 'EST': 'EST',
        'EQUIPAMENTO DE VOO': 'EQV', 'EQV': 'EQV',
        'ARMAMENTO': 'ARM', 'ARM': 'ARM',
        'TODAS': 'TODAS'
    }
    parts = [p.strip().upper() for p in esp_string.split(';')]
    codes = set()
    for p in parts:
        if not p: continue
        codes.add(mapping.get(p, p))
            
    core = {'MOT', 'CEL', 'HID', 'ELT', 'ELE', 'EST', 'EQV', 'ARM'}
    if core.issubset(codes) or 'TODAS' in codes:
        return ['TODAS']
        
    return sorted(list(codes))

templates.env.globals["csrf_token"] = get_csrf_token
templates.env.filters['format_especialidade'] = format_especialidade
