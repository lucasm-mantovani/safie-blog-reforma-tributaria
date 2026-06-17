"""
buscar_noticia.py — Fase 3 do pipeline diário (Blog Reforma Tributária)

Fluxo:
  1. Para cada tema em config/temas.json, busca notícias via RSS
  2. Filtra resultados das últimas 48h
  3. Seleciona a notícia mais relevante (sem repetir histórico dos últimos 15 dias)
  4. Se RSS não trouxer notícia fresca → encerra com exit 75 (Direção 1: sem evergreen, não publica)
  5. Prioridade: fontes oficiais e regulatórias, depois grandes veículos

Uso:
  python3 scripts/buscar_noticia.py
  python3 scripts/buscar_noticia.py --tema ibs-cbs
"""

import json
import os
import sys
import argparse
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict

import feedparser
from dotenv import load_dotenv

# ── Caminhos ──────────────────────────────────────────────────────────────────
BASE           = Path(__file__).resolve().parent.parent
CONFIG_BLOG    = BASE / "config" / "blog.json"
CONFIG_TEMAS   = BASE / "config" / "temas.json"
CONFIG_FONTES  = BASE / "config" / "fontes.json"
HISTORICO      = BASE / "dados" / "historico_noticias.json"
LOG_DIR        = BASE / "logs"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)
hoje = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"busca_{hoje}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

load_dotenv(BASE / ".env")
load_dotenv(Path.home() / ".zshrc", override=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def ler_json(caminho: Path, padrao):
    if caminho.exists():
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Erro ao ler {caminho}: {e}")
    return padrao


def salvar_json(caminho: Path, dados):
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Histórico ─────────────────────────────────────────────────────────────────

def ja_publicado(url: str, tema_slug: str,
                 dias_url: int = 15, dias_tema: int = 3) -> bool:
    """
    Retorna True se URL ou tema_slug já foi publicado dentro
    de sua respectiva janela de tempo.
    - dias_url: janela em dias para bloquear mesma URL (default 15)
    - dias_tema: janela em dias para espaçar mesmo tema (default 3)
    Entradas com url_fonte ou tema_slug vazios são ignoradas.
    Entradas com data_publicacao inválida são ignoradas.
    """
    dados = ler_json(HISTORICO, {"noticias": []})
    agora = datetime.now(timezone.utc)
    limite_url = agora - timedelta(days=dias_url)
    limite_tema = agora - timedelta(days=dias_tema)

    for item in dados.get("noticias", []):
        item_url = item.get("url_fonte", "")
        item_tema = item.get("tema_slug", "")
        data_str = item.get("data_publicacao", "")

        try:
            data_pub = datetime.fromisoformat(data_str)
        except (ValueError, TypeError):
            continue

        if url and item_url == url and data_pub >= limite_url:
            return True

        if tema_slug and item_tema == tema_slug and data_pub >= limite_tema:
            return True

    return False


def registrar_noticia_publicada(noticia: dict):
    dados = ler_json(HISTORICO, {"noticias": []})
    dados["noticias"].append({
        "data_publicacao": datetime.now(timezone.utc).isoformat(),
        "titulo_noticia": noticia.get("titulo", ""),
        "url_fonte": noticia.get("url", ""),
        "tema_slug": noticia.get("tema_slug", ""),
    })
    dados["noticias"] = dados["noticias"][-90:]
    salvar_json(HISTORICO, dados)


# ── RSS ───────────────────────────────────────────────────────────────────────

def buscar_rss(tema: Dict, fontes: List[Dict]) -> List[Dict]:
    """
    Percorre os feeds RSS e filtra itens das últimas 48h
    que contenham alguma palavra-chave do tema.

    Regra: o artigo deve conter PELO MENOS uma frase-chave inteira do tema
    (todas as palavras da frase presentes no texto) E pelo menos um termo
    base que confirme relação com reforma tributária.
    """
    # Termos base obrigatórios — sem ao menos um deles, o artigo é descartado
    TERMOS_BASE = [
        "reforma tributária", "reforma tributaria",
        " ibs ", "ibs,", "o ibs", "do ibs",
        " cbs ", "cbs,", "a cbs", "da cbs",
        "imposto seletivo",
        "split payment",
        "comitê gestor",
        "simples nacional reforma",
        "transição tributária", "transicao tributaria",
        "lei complementar 214", "lei complementar 68",
        "pis/cofins", "fim do icms", "fim do iss",
        "não cumulatividade",
    ]

    limite = datetime.now(timezone.utc) - timedelta(hours=48)
    resultados = []

    for fonte in fontes:
        log.info(f"[RSS] Lendo {fonte['nome']}...")
        try:
            feed = feedparser.parse(fonte["url"])
            for entry in feed.entries:
                texto = (
                    (entry.get("title") or "") + " " +
                    (entry.get("summary") or "")
                ).lower()

                # Filtro obrigatório: deve mencionar reforma tributária de fato
                if not any(t in texto for t in TERMOS_BASE):
                    continue

                # Filtro de tema: ao menos UMA frase-chave com todas as palavras presentes
                frase_bateu = False
                for frase in tema.get("palavras_chave", []):
                    palavras_frase = [p for p in frase.lower().split() if len(p) >= 4]
                    if palavras_frase and all(p in texto for p in palavras_frase):
                        frase_bateu = True
                        break
                if not frase_bateu:
                    continue

                data_entry = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    ts = time.mktime(entry.published_parsed)
                    data_entry = datetime.fromtimestamp(ts, tz=timezone.utc)

                if data_entry and data_entry < limite:
                    continue

                resultados.append({
                    "titulo": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "fonte": fonte["nome"],
                    "data": data_entry.isoformat() if data_entry else "",
                    "resumo": entry.get("summary", "")[:300],
                    "tema_slug": tema["slug"],
                    "tema_nome": tema["nome"],
                    "origem": "rss",
                })

        except Exception as e:
            log.warning(f"[RSS] Erro em {fonte['nome']}: {e}")

    log.info(f"[RSS] {len(resultados)} resultado(s) para tema '{tema['nome']}'")
    return resultados


# ── Pontuação de relevância ───────────────────────────────────────────────────

# Fontes com maior autoridade para reforma tributária
FONTES_AUTORIDADE = {
    "valor.globo.com": 10,
    "jota.info": 10,
    "migalhas.com.br": 9,
    "conjur.com.br": 9,
    "infomoney.com.br": 8,
    "exame.com": 7,
    "gov.br": 12,          # fontes oficiais têm prioridade máxima
    "receita.fazenda.gov.br": 12,
    "camara.leg.br": 11,
    "senado.leg.br": 11,
    "stf.jus.br": 11,
    "stj.jus.br": 10,
    "carf.fazenda.gov.br": 10,
}

# Palavras que indicam conteúdo técnico prioritário (não especulação política)
PALAVRAS_TECNICAS = [
    "lei complementar", "regulamentação", "decreto", "portaria", "instrução normativa",
    "ibs", "cbs", "imposto seletivo", "split payment", "comitê gestor",
    "alíquota", "base de cálculo", "contribuinte", "não cumulatividade",
    "transição", "período transitório", "simples nacional", "mei",
    "stf", "stj", "carf", "acórdão", "decisão judicial",
    "receita federal", "fazenda", "sefaz",
]

# Palavras que indicam conteúdo político sem impacto técnico (penalizar)
PALAVRAS_POLITICAS = [
    "eleição", "partido", "candidato", "campanha", "voto", "plenário político",
    "oposição", "governo critica", "deputado diz", "senador afirma",
]


def pontuar_noticia(noticia: dict) -> float:
    texto = (noticia.get("titulo", "") + " " + noticia.get("resumo", "")).lower()
    url = noticia.get("url", "").lower()
    fonte = noticia.get("fonte", "").lower()
    pontos = 0.0

    # Autoridade da fonte
    for dominio, score in FONTES_AUTORIDADE.items():
        if dominio in url or dominio in fonte:
            pontos += score
            break

    # Relevância técnica
    for palavra in PALAVRAS_TECNICAS:
        if palavra in texto:
            pontos += 3

    # Penalizar conteúdo puramente político
    for palavra in PALAVRAS_POLITICAS:
        if palavra in texto:
            pontos -= 4

    # Recência
    data_str = noticia.get("data", "")
    if data_str:
        try:
            data = datetime.fromisoformat(data_str)
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)
            horas_atras = (datetime.now(timezone.utc) - data).total_seconds() / 3600
            if horas_atras < 6:
                pontos += 8
            elif horas_atras < 24:
                pontos += 4
        except Exception:
            pass

    # Penalizar ausência de resumo
    if not noticia.get("resumo"):
        pontos -= 3

    return pontos


# ── Seleção ───────────────────────────────────────────────────────────────────

def selecionar_melhor(candidatos: List[Dict]) -> Optional[Dict]:
    validos = [
        c for c in candidatos
        if c.get("url") and not ja_publicado(c["url"], c.get("tema_slug", ""))
    ]

    if not validos:
        return None

    validos.sort(key=pontuar_noticia, reverse=True)
    escolhida = validos[0]
    log.info(f"Notícia selecionada: [{escolhida['tema_nome']}] {escolhida['titulo']}")
    return escolhida


# ── Orquestrador principal ────────────────────────────────────────────────────

def main(apenas_tema: str = "") -> Dict:
    log.info("=" * 60)
    log.info("BUSCAR NOTÍCIA — início")

    # Higiene: limpar saída anterior para evitar consumo ambíguo (Direção 1)
    arquivo_saida = BASE / "dados" / "noticia_selecionada.json"
    if arquivo_saida.exists():
        arquivo_saida.unlink()

    config_temas  = ler_json(CONFIG_TEMAS, {"temas": []})
    config_fontes = ler_json(CONFIG_FONTES, {"rss_feeds": []})

    temas      = config_temas.get("temas", [])
    fontes_rss = config_fontes.get("rss_feeds", [])

    if apenas_tema:
        temas = [t for t in temas if t["slug"] == apenas_tema]
        if not temas:
            log.error(f"Tema '{apenas_tema}' não encontrado em config/temas.json")
            sys.exit(1)

    todos_candidatos = []

    log.info("Buscando via RSS...")
    for tema in temas:
        resultados_rss = buscar_rss(tema, fontes_rss)
        todos_candidatos.extend(resultados_rss)

    noticia = selecionar_melhor(todos_candidatos)

    # Sem notícia fresca → não publica hoje (Direção 1, sem evergreen)
    if not noticia:
        log.warning("Nenhuma notícia nova encontrada hoje. Encerrando sem publicar (exit 75).")
        sys.exit(75)

    log.info("=" * 60)
    log.info(f"RESULTADO FINAL:")
    log.info(f"  Tema:   {noticia.get('tema_nome')}")
    log.info(f"  Título: {noticia.get('titulo')}")
    log.info(f"  Fonte:  {noticia.get('fonte')} ({noticia.get('origem')})")
    log.info(f"  URL:    {noticia.get('url') or '(sem URL)'}")
    log.info("=" * 60)

    resultado_path = BASE / "dados" / "noticia_selecionada.json"
    salvar_json(resultado_path, noticia)
    log.info(f"Resultado salvo em {resultado_path}")

    if noticia.get("url"):
        try:
            registrar_noticia_publicada(noticia)
        except Exception as e:
            log.warning(f"[aviso] falha ao registrar histórico: {e}")

    print(json.dumps(noticia, ensure_ascii=False, indent=2))
    return noticia


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busca notícia para o artigo diário")
    parser.add_argument("--tema", default="", help="Slug do tema específico (ex: ibs-cbs)")
    args = parser.parse_args()

    main(apenas_tema=args.tema)
