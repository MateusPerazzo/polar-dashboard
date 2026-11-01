import pandas as pd

RECHARGE_STATUS = {
    1: "muito ruim", 2: "ruim", 3: "comprometida", 4: "OK", 5: "boa", 6: "muito boa",
}
# Escala da Polar para ans_charge_status e sleep_charge (comparação com o seu padrão).
USUAL_SCALE = {
    1: "muito abaixo do usual", 2: "abaixo do usual", 3: "usual",
    4: "acima do usual", 5: "muito acima do usual",
}
CONTINUITY_CLASS = {
    1: "fragmentado", 2: "um pouco fragmentado", 3: "razoavelmente contínuo",
    4: "contínuo", 5: "muito contínuo",
}
# Códigos da API -> faixa do hipnograma. 2 (não-REM mais leve) e 3 (não-REM leve)
# viram "Leve"; o 5 (indefinido, ex.: mau contato) fica sem faixa e vira um vão.
STAGE_BY_CODE = {0: "Acordado", 1: "REM", 2: "Leve", 3: "Leve", 4: "Profundo"}

# Mensagens e personagem de cada status do Nightly Recharge (1 = muito ruim ... 6 = muito boa).
# Os conselhos seguem as dicas do app da Polar para cada nível.
LEVELS = {
    1: {
        "headline": "Até a juventude precisa de pausa.",
        "summary": "Sua recuperação ficou muito abaixo do normal esta noite.",
        "advice": "Descanse ou faça só um treino bem leve, e tente dormir mais cedo hoje.",
        "character": "Rock Lee", "mood": "completamente exausto",
        "quote": "O fogo da juventude não se apaga com um dia ruim. Amanhã eu volto em dobro!",
    },
    2: {
        "headline": "Hora de baixar a espada.",
        "summary": "Sua recuperação ficou abaixo do normal esta noite.",
        "advice": "Respeite a necessidade do seu corpo e treine leve. Descansar também vale.",
        "character": "Guts", "mood": "marcado pela batalha, mas de pé",
        "quote": "Enquanto houver fôlego, eu sigo em frente. Não importa a tempestade: lute!",
    },
    3: {
        "headline": "Cansado, mas sem desistir.",
        "summary": "Sua recuperação ficou um pouco abaixo do normal esta noite.",
        "advice": "Dá para treinar, desde que você ouça o seu corpo e evite exageros.",
        "character": "Asta", "mood": "cansado, mas ainda determinado",
        "quote": "Não desistir é a minha magia! Vou superar meus limites aqui e agora!",
    },
    4: {
        "headline": "Dia para manter o ritmo.",
        "summary": "Sua recuperação está dentro do normal.",
        "advice": "É um bom dia para treinar. Siga o planejado, sem exageros.",
        "character": "Luffy", "mood": "relaxado e de boa",
        "quote": "Eu sou o homem que vai se tornar o Rei dos Piratas!",
    },
    5: {
        "headline": "Você está pronto para avançar.",
        "summary": "Seu corpo se recuperou bem esta noite.",
        "advice": "Vá com tudo: é um bom dia para aumentar a intensidade.",
        "character": "Satoru Gojo", "mood": "confiante e com disposição",
        "quote": "Entre o céu e a terra, sou o mais honrado.",
    },
    6: {
        "headline": "Você está no auge.",
        "summary": "Seu corpo se recuperou muito bem esta noite.",
        "advice": "Hoje é um dia incrível para se exercitar, inclusive para o treino mais forte da semana.",
        "character": "Goku Super Saiyajin Blue", "mood": "no auge",
        "quote": "Oi, eu sou o Goku! Hoje dá para ir além do limite. Vamos treinar!",
    },
}
# Máximo de caracteres de cada texto, para caber na sua seção de altura fixa no Insight do dia
# (título: 1 linha; conselho: completa as 4 linhas do texto; personagem e humor: 1 linha;
# fala: 2 linhas) e, a frase do topo, em 1 linha ao lado da barra do topo. Usado como
# max_chars em Configurações.
TEXT_LIMITS = {"headline": 34, "summary": 64, "advice": 90, "character": 24, "mood": 32, "quote": 80}


def classify(status):
    if pd.isna(status):
        return "neutral"
    if status >= 5:
        return "good"
    if status == 4:
        return "neutral"
    return "low"


def stage_segments(hypnogram, night_end):
    """Transforma as mudanças de estágio em trechos (estágio, início, fim)."""
    segments = pd.DataFrame({
        "stage": hypnogram["stage"].map(STAGE_BY_CODE),
        "start": hypnogram["timestamp"],
        "end": hypnogram["timestamp"].shift(-1).fillna(night_end),
    })
    # Trechos seguidos do mesmo estágio viram um só (ex.: "mais leve" + "leve").
    block = (segments["stage"] != segments["stage"].shift()).cumsum()
    merged = segments.groupby(block).agg(
        stage=("stage", "first"), start=("start", "first"), end=("end", "last"),
    )
    return merged.dropna(subset=["stage"])


def build_insight(sleep, recharge, night=None, levels=LEVELS):
    """night: data da noite a mostrar; None = a mais recente. A média usa só noites anteriores.
    levels: mensagens por status (padrão LEVELS; Configurações passa as personalizadas)."""
    if recharge.empty:
        return None
    is_latest = night is None or night >= recharge["date"].max()
    if not is_latest:
        recharge = recharge[recharge["date"] <= night]
        if recharge.empty:
            return None
    last = recharge.iloc[-1]
    status = None if pd.isna(last["nightly_recharge_status"]) else int(last["nightly_recharge_status"])
    state = classify(status)
    # Sem status (a Polar ainda não calculou): mensagens do nível OK, sem personagem.
    no_status = {key: levels[4][key] for key in ("headline", "summary", "advice")}
    level = levels.get(status, no_status)

    facts = []
    hrv_baseline = recharge["heart_rate_variability_avg"].iloc[-8:-1].mean()
    if pd.notna(hrv_baseline) and hrv_baseline:
        change = (last["heart_rate_variability_avg"] - hrv_baseline) / hrv_baseline * 100
        direction = "acima" if change >= 0 else "abaixo"
        facts.append(f"seu HRV ficou {abs(change):.0f}% {direction} da sua média dos últimos 7 dias")
    same_night = sleep[sleep["date"] == last["date"]]
    if not same_night.empty:
        facts.append(f"a nota do sono foi {same_night['sleep_score'].iloc[0]:.0f}")

    text = level["advice"]
    if facts:
        opener = "Esta noite" if is_latest else f"Na noite de {last['date']:%d/%m}"
        text = f"{opener}, {' e '.join(facts)}. {text}"

    return {
        "state": state,
        "date": last["date"],
        "status": status,
        "status_label": RECHARGE_STATUS.get(status, "—"),
        "headline": level["headline"],
        "summary": level["summary"],
        "text": text,
        # Personagem do nível; None quando não há status.
        "character": level.get("character"),
        "mood": level.get("mood"),
        "quote": level.get("quote"),
    }
