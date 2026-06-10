# IoMT-FL Consensus Tool

Ferramenta em Python para simulação de dispositivos IoHT, consenso e agregação em Federated Learning.

## Componentes
- Simulador de clientes IoHT
- Servidor FL
- Agregadores: FedAvg, Weighted, Robust, MultiKrum
- Módulos de consenso: Threshold, Voting, HotStuff BFT
- Geração de dados sintéticos com drift não-IID
- Execução de cenários experimentais
- Exportação de métricas em CSV e JSON
- Demonstração reproduzível por linha de comando

## Estrutura
```
├── src/iomt_fl_consensus/ # Código-fonte (domain-driven)
│   ├── core/              #   FLServer, IoHTClient, modelos
│   ├── aggregation/       #   FedAvg, Weighted, Robust, MultiKrum
│   ├── consensus/         #   Threshold, Voting, HotStuff
│   ├── data/              #   Geração de dados sintéticos
│   └── runner/            #   ExperimentRunner e logging
├── config/                # Cenários de configuração (JSON)
├── results/               # Saídas experimentais (CSV, JSON)
├── docs/                  # Documentação técnica
├── latex_demo/            # Artigo técnico .tex/.bib
├── tests/                 # Testes básicos
└── scripts/               # Scripts auxiliares
```

## Execução rápida
```bash
python scripts/run_demo.py --config config/scenario_baseline.json
```

### Cenários disponíveis
| Config | Agregador | Consenso | Descrição |
|--------|-----------|----------|-----------|
| `scenario_baseline.json` | FedAvg | Threshold | IID, sem falhas |
| `scenario_non_iid.json` | Weighted | Voting | Não-IID, weighted |
| `scenario_robust.json` | Robust | Threshold | Com falhas |
| `scenario_multi_krum.json` | MultiKrum | Threshold | Tolerância Bizantina |
| `scenario_hotstuff.json` | FedAvg | HotStuff | Consenso BFT |

## Requisitos
Python 3.10+

Bibliotecas padrão utilizadas: `json`, `math`, `random`, `statistics`, `csv`, `argparse`, `pathlib`, `dataclasses`.

## Saídas
A execução gera:
- `results/*.csv` (métricas por rodada)
- `results/*.json` (resumo do experimento)
- logs do experimento no terminal (nível, formato e arquivo configuráveis)
