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
├── scripts/               # Scripts de execução
│   ├── run_demo.py        #   Single-process (local)
│   ├── edge_service.py    #   Servidor HTTP da camada Edge
│   ├── fog_service.py     #   Servidor HTTP da camada Fog
│   └── cloud_service.py   #   Orquestrador da camada Cloud
├── config/                # Cenários de configuração (JSON)
├── results/               # Saídas experimentais (CSV, JSON)
├── docs/                  # Documentação técnica
├── tests/                 # Testes básicos
└── docker-compose.yml     # Orquestração multi-container
```

## Execução

### Modo local (single-process)
```bash
python scripts/run_demo.py --config config/scenario_baseline.json
```

A config também pode vir de variáveis de ambiente (`CONFIG_*`):
```bash
CONFIG_NAME=env_test CONFIG_NUM_CLIENTS=10 CONFIG_ROUNDS=3 \
  CONFIG_AGGREGATOR=fedavg CONFIG_CONSENSUS=threshold \
  python scripts/run_demo.py
```

### Modo Docker (3 camadas em containers separados)
```bash
docker compose up --build
```

Cada camada executa em um container independente com comunicação HTTP:
- **Edge** (porta 8000): gerencia N clientes IoHT, treinamento local
- **Fog** (porta 8001): valida updates via módulo de consenso
- **Cloud**: orquestra rodadas, agrega, exporta resultados

A configuração de cada serviço é feita via variáveis de ambiente no `docker-compose.yml`.

### Cenários disponíveis

#### Modo local (arquivos JSON)
| Config | Agregador | Consenso | Descrição |
|--------|-----------|----------|-----------|
| `scenario_baseline.json` | FedAvg | Threshold | IID, sem falhas |
| `scenario_non_iid.json` | Weighted | Voting | Não-IID, weighted |
| `scenario_robust.json` | Robust | Threshold | Com falhas |
| `scenario_multi_krum.json` | MultiKrum | Threshold | Tolerância Bizantina |
| `scenario_hotstuff.json` | FedAvg | HotStuff | Consenso BFT |

#### Modo Docker (variáveis de ambiente)
Edite as variáveis `CONFIG_*` no `docker-compose.yml` para alterar agregador, consenso, número de clientes, etc.

## Requisitos
Python 3.10+

Bibliotecas padrão utilizadas: `json`, `math`, `random`, `statistics`, `csv`, `argparse`, `pathlib`, `dataclasses`.

## Arquitetura em camadas

A ferramenta simula uma arquitetura Edge-Fog-Cloud com duas formas de execução:

**Single-process (local):** `ExperimentRunner` orquestra tudo no mesmo processo:
`IoHTClient → ConsensusModule → Aggregator → export CSV/JSON`

**Docker multi-container:** cada camada é um serviço HTTP independente:
```
Cloud (orquestrador)  ──POST /train──►  Edge (clientes IoHT)
     │                                    porta 8000
     └─────────POST /validate──────────►  Fog (consenso)
                                           porta 8001
```

## Saídas
A execução gera:
- `results/*.csv` (métricas por rodada)
- `results/*.json` (resumo do experimento)
- logs do experimento no terminal (nível, formato e arquivo configuráveis)
