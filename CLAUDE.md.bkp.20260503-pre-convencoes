# CLAUDE.md — Blog-reforma-tributaria SAFIE

## O que é este projeto
Blog automatizado em HTML estático, publicado em **reformatributaria.safie.blog.br**, com artigos gerados diariamente via Claude API.
O blog cobre os impactos da reforma tributária brasileira (EC 132/2023) para empresas, com foco em IBS, CBS, Imposto Seletivo e o período de transição.

## ATENÇÃO: domínios completamente diferentes

| Domínio | O que é | Pode alterar? |
|---|---|---|
| safie.com.br | Site institucional da SAFIE | **NUNCA** |
| safie.blog.br | Rede de blogs temáticos | Sim, é este projeto |
| reformatributaria.safie.blog.br | Este blog específico | Sim |

**NUNCA modifique, acesse para edição ou mencione safie.com.br como destino de qualquer ação de código.**

## Estrutura de pastas

```
Blog-reforma-tributaria/
├── config/          # blog.json, temas.json, fontes.json
├── dados/           # historico_noticias.json, noticia_selecionada.json, artigo_gerado.json
├── templates/       # artigo.html, tema.html
├── assets/
│   ├── css/         # estilo.css (identidade SAFIE)
│   ├── js/          # busca.js
│   └── img/         # favicon.svg
├── artigos/         # HTMLs gerados + indice.json
├── temas/           # Páginas de listagem por tema
├── scripts/
│   ├── buscar_noticia.py
│   ├── gerar_artigo.py
│   └── publicar.py
├── logs/            # Logs diários (não versionados)
├── rodar_diario.sh  # Orquestrador (launchd às 8h15)
├── sitemap.xml
├── robots.txt
├── .env             # Credenciais (NÃO versionado)
└── .env.template    # Modelo de credenciais
```

## Credenciais necessárias (.env)
- `ANTHROPIC_API_KEY` — geração de artigos via Claude API
- `GITHUB_TOKEN` — push automático dos artigos
- `GITHUB_REPO` — formato `lucasm-mantovani/safie-blog-reforma-tributaria`

**Nunca hardcode credenciais.**

## Pipeline diário (rodar_diario.sh — executa às 8h15 via launchd)
1. `buscar_noticia.py` — busca notícias via RSS (8 temas, fontes especializadas)
2. `gerar_artigo.py` — gera artigo via Claude API
3. `publicar.py` — gera HTML, atualiza home/sitemap, commit + push GitHub

## Temas cobertos
1. IBS e CBS — novos tributos (slug: ibs-cbs)
2. Imposto Seletivo (slug: imposto-seletivo)
3. Transição tributária 2026-2033 (slug: transicao-tributaria)
4. Split payment e fiscalização (slug: split-payment)
5. Setores específicos e a reforma (slug: setores-reforma)
6. Regimes especiais e o Simples Nacional (slug: simples-reforma)
7. Compliance e adaptação das empresas (slug: compliance-reforma)
8. Regulamentação infralegal (slug: regulamentacao)

## Regras de SEO e GEO
- Título: máximo 60 caracteres
- Meta description: máximo 155 caracteres
- Estrutura: resumo executivo → contexto jurídico → impacto prático → FAQ (3-5 perguntas)
- Schema.org: BlogPosting + FAQPage em JSON-LD
- URL: `https://reformatributaria.safie.blog.br/artigos/AAAA-MM-DD-slug`
- Artigos: mínimo 800, máximo 1.500 palavras

## Filtragem de notícias (prioridade)
1. Fontes oficiais (gov.br, Receita Federal, Congresso)
2. Decisões judiciais (STF, STJ, CARF)
3. Leis complementares e regulamentações
4. Análises de grandes veículos (Valor, JOTA, Migalhas, Conjur)

Evitar: notícias puramente políticas, especulações sem ato oficial, conteúdo repetitivo de agências.

## Estado atual do projeto (2026-04-24)
- **Fase 1 concluída:** Estrutura de pastas, configs, templates HTML, scripts Python, rodar_diario.sh
- **Fase 2 concluída:** Interface HTML/CSS (identidade SAFIE), visual validado no browser
- **Fase 3 concluída:** buscar_noticia.py — RSS funcionando, duplo filtro (base + tema) implementado
- **Fase 4 concluída:** Pipeline completo testado — primeiro artigo gerado e publicado localmente
- **Fase 5 concluída:**
  - GitHub: https://github.com/lucasm-mantovani/safie-blog-reforma-tributaria (no ar)
  - Cron job (launchd): configurado, roda todo dia às 8h15
  - Cloudflare Pages: no ar (safie-blog-reforma-tributaria.pages.dev)
  - Domínio: reformatributaria.safie.blog.br (DNS propagado em 2026-04-28)
- **Fase 6 concluída (2026-04-28):**
  - DNS propagado e HTTP 200 confirmados
  - robots.txt + sitemap.xml funcionando
  - Schema.org BlogPosting + FAQPage em todos os artigos
  - meta robots, keywords, og:*, twitter:* no template
  - Validação manual opcional: Google Rich Results Test + PageSpeed Insights
