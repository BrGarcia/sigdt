from typing import Dict, List

class Especialidade:
    """
    Classe centralizadora para as especialidades técnicas do sistema SIGDT.
    Mapeia siglas curtas para nomes extensos e vice-versa.
    """
    
    # Mapeamento oficial: Sigla -> Nome Extenso
    MAPA: Dict[str, str] = {
        'ELT': 'ELETRÔNICA',
        'ELE': 'ELÉTRICA',
        'HID': 'HIDRÁULICA',
        'CEL': 'CÉLULA',
        'MOT': 'MOTORES',
        'EST': 'ESTRUTURA',
        'EQV': 'EQUIPAMENTO DE VOO',
        'ARM': 'ARMAMENTO',
    }

    # Mapeamento reverso para normalização (incluindo variações sem acento)
    REVERSO: Dict[str, str] = {
        'ELETRÔNICA': 'ELT', 'ELETRONICA': 'ELT', 'ELT': 'ELT',
        'ELÉTRICA': 'ELE', 'ELETRICA': 'ELE', 'ELE': 'ELE',
        'HIDRÁULICA': 'HID', 'HIDRAULICA': 'HID', 'HID': 'HID',
        'CÉLULA': 'CEL', 'CELULA': 'CEL', 'CEL': 'CEL',
        'MOTORES': 'MOT', 'MOT': 'MOT',
        'ESTRUTURA': 'EST', 'EST': 'EST',
        'EQUIPAMENTO DE VOO': 'EQV', 'EQV': 'EQV',
        'ARMAMENTO': 'ARM', 'ARM': 'ARM',
        'TODAS': 'TODAS'
    }

    @classmethod
    def list_codes(cls) -> List[str]:
        """Retorna apenas as siglas (ex: ELT, ELE)."""
        return sorted(list(cls.MAPA.keys()))

    @classmethod
    def get_label(cls, code: str) -> str:
        """Retorna o nome por extenso a partir da sigla."""
        return cls.MAPA.get(code.upper(), code)

    @classmethod
    def normalize(cls, name: str) -> str:
        """Normaliza um nome ou sigla para a sigla padrão (ex: 'Elétrica' -> 'ELE')."""
        if not name:
            return ""
        return cls.REVERSO.get(name.strip().upper(), name.strip().upper())
