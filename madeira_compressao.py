"""Verificação de peça de madeira comprimida com parâmetros da NBR 7190:2022.

Entradas do usuário:
1) Base e altura da seção (mm)
2) Classe de resistência da madeira (ex.: C20, C30, D18, D40)
3) Carga de compressão axial de cálculo (kN)
4) Classe de umidade (1, 2 ou 3)
5) Duração do carregamento (permanente, longa, média, curta, instantânea)

Observação importante:
- Esta implementação contempla a verificação resistente por tensão média à
  compressão paralela às fibras (N_d / A <= f_c0,d), com fatores kmod1 e kmod2
  tabelados no código e gamma_w = 1.4 por padrão.
- Verificações de estabilidade (ex.: flambagem), que exigem dados geométricos
  adicionais (como comprimento de flambagem e vinculações), não são cobertas por
  falta de entradas correspondentes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClasseMadeira:
    """Propriedades características por classe de resistência (MPa e kg/m³)."""

    classe: str
    tipo: str
    f_c0k_mpa: float
    f_t0k_mpa: float
    f_vk_mpa: float
    e_m0_mpa: float
    densidade_basica_kg_m3: float
    densidade_aparente_kg_m3: float


# Classes de resistência estruturais (coníferas Cxx e folhosas Dxx).
# Valores catalogados no código para uso direto no cálculo.
CLASSES_MADEIRA: dict[str, ClasseMadeira] = {
    "C20": ClasseMadeira("C20", "Conífera", 20.0, 12.0, 4.0, 9500, 400, 500),
    "C25": ClasseMadeira("C25", "Conífera", 25.0, 15.0, 4.5, 10500, 430, 540),
    "C30": ClasseMadeira("C30", "Conífera", 30.0, 18.0, 5.0, 11500, 460, 560),
    "C40": ClasseMadeira("C40", "Conífera", 40.0, 24.0, 6.0, 13000, 500, 620),
    "C60": ClasseMadeira("C60", "Conífera", 60.0, 36.0, 8.0, 16000, 600, 750),
    "D18": ClasseMadeira("D18", "Folhosa", 18.0, 11.0, 4.0, 9000, 500, 650),
    "D24": ClasseMadeira("D24", "Folhosa", 24.0, 14.0, 4.5, 10500, 550, 700),
    "D30": ClasseMadeira("D30", "Folhosa", 30.0, 18.0, 5.0, 12000, 620, 770),
    "D40": ClasseMadeira("D40", "Folhosa", 40.0, 24.0, 6.0, 14500, 700, 850),
    "D50": ClasseMadeira("D50", "Folhosa", 50.0, 30.0, 7.0, 17000, 780, 940),
    "D60": ClasseMadeira("D60", "Folhosa", 60.0, 36.0, 8.0, 19500, 850, 1020),
}


# Tabela kmod1 (dependente da duração do carregamento).
KMOD1_POR_DURACAO: dict[str, float] = {
    "permanente": 0.60,
    "longa": 0.70,
    "media": 0.80,
    "média": 0.80,
    "curta": 0.90,
    "instantanea": 1.10,
    "instantânea": 1.10,
}


# Tabela kmod2 (dependente da classe de umidade).
KMOD2_POR_UMIDADE: dict[int, float] = {
    1: 1.00,
    2: 0.90,
    3: 0.80,
}


def verificar_compressao_nbr7190(
    base_mm: float,
    altura_mm: float,
    classe_madeira: str,
    carga_compressao_kn: float,
    classe_umidade: int,
    duracao_carregamento: str,
    gamma_w: float = 1.4,
) -> dict[str, float | str | bool]:
    """Verifica compressão paralela às fibras pela expressão resistente de projeto.

    Cálculos executados:
    - A = base * altura
    - sigma_c0,d = N_d / A
    - kmod = kmod1 * kmod2
    - f_c0,d = kmod * f_c0,k / gamma_w
    - critério: sigma_c0,d <= f_c0,d
    """
    chave_classe = classe_madeira.strip().upper()
    if chave_classe not in CLASSES_MADEIRA:
        classes = ", ".join(sorted(CLASSES_MADEIRA.keys()))
        raise ValueError(f"Classe de madeira inválida. Opções: {classes}")

    if base_mm <= 0 or altura_mm <= 0:
        raise ValueError("Base e altura devem ser maiores que zero.")
    if carga_compressao_kn <= 0:
        raise ValueError("A carga de compressão deve ser maior que zero.")

    if classe_umidade not in KMOD2_POR_UMIDADE:
        raise ValueError("Classe de umidade inválida. Use 1, 2 ou 3.")

    chave_duracao = duracao_carregamento.strip().lower()
    if chave_duracao not in KMOD1_POR_DURACAO:
        duracoes = ", ".join(sorted(KMOD1_POR_DURACAO.keys()))
        raise ValueError(f"Duração do carregamento inválida. Opções: {duracoes}")

    madeira = CLASSES_MADEIRA[chave_classe]
    kmod1 = KMOD1_POR_DURACAO[chave_duracao]
    kmod2 = KMOD2_POR_UMIDADE[classe_umidade]
    kmod = kmod1 * kmod2

    area_mm2 = base_mm * altura_mm
    n_d_n = carga_compressao_kn * 1000
    sigma_c0d_mpa = n_d_n / area_mm2
    f_c0d_mpa = (kmod * madeira.f_c0k_mpa) / gamma_w

    utilizacao = sigma_c0d_mpa / f_c0d_mpa
    aprovado = sigma_c0d_mpa <= f_c0d_mpa

    return {
        "classe_madeira": madeira.classe,
        "tipo_madeira": madeira.tipo,
        "base_mm": base_mm,
        "altura_mm": altura_mm,
        "area_mm2": area_mm2,
        "n_d_n": n_d_n,
        "classe_umidade": classe_umidade,
        "duracao_carregamento": chave_duracao,
        "kmod1": kmod1,
        "kmod2": kmod2,
        "kmod": kmod,
        "gamma_w": gamma_w,
        "f_c0k_mpa": madeira.f_c0k_mpa,
        "sigma_c0d_mpa": sigma_c0d_mpa,
        "f_c0d_mpa": f_c0d_mpa,
        "utilizacao": utilizacao,
        "aprovado": aprovado,
    }


def solicitar_dados_usuario() -> tuple[float, float, str, float, int, str]:
    print("=== Entrada de dados NBR 7190:2022 - Compressão ===")
    print("Classes disponíveis:", ", ".join(sorted(CLASSES_MADEIRA.keys())))

    base_mm = float(input("Base da peça (mm): "))
    altura_mm = float(input("Altura da peça (mm): "))
    classe_madeira = input("Classe de resistência da madeira (ex.: D18, C30): ")
    carga_compressao_kn = float(input("Carregamento de compressão axial Nd (kN): "))
    classe_umidade = int(input("Classe de umidade (1, 2 ou 3): "))
    duracao_carregamento = input(
        "Duração do carregamento (permanente/longa/média/curta/instantânea): "
    )

    return (
        base_mm,
        altura_mm,
        classe_madeira,
        carga_compressao_kn,
        classe_umidade,
        duracao_carregamento,
    )


def main() -> None:
    dados = solicitar_dados_usuario()
    resultado = verificar_compressao_nbr7190(*dados)

    print("\n--- Resultado da verificação (NBR 7190:2022) ---")
    print(f"Classe: {resultado['classe_madeira']} ({resultado['tipo_madeira']})")
    print(f"Seção: {resultado['base_mm']:.2f} x {resultado['altura_mm']:.2f} mm")
    print(f"Área: {resultado['area_mm2']:.2f} mm²")
    print(f"Nd: {resultado['n_d_n']:.2f} N")
    print(f"kmod1: {resultado['kmod1']:.3f}")
    print(f"kmod2: {resultado['kmod2']:.3f}")
    print(f"kmod = kmod1*kmod2: {resultado['kmod']:.3f}")
    print(f"gamma_w: {resultado['gamma_w']:.2f}")
    print(f"f_c0,k: {resultado['f_c0k_mpa']:.3f} MPa")
    print(f"sigma_c0,d = Nd/A: {resultado['sigma_c0d_mpa']:.3f} MPa")
    print(f"f_c0,d = kmod*f_c0,k/gamma_w: {resultado['f_c0d_mpa']:.3f} MPa")
    print(f"Taxa de utilização: {resultado['utilizacao'] * 100:.1f}%")
    print("Status:", "APROVADO" if resultado["aprovado"] else "REPROVADO")


if __name__ == "__main__":
    main()
