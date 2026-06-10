# Arquitetura da Ferramenta

## Diagrama de Classes UML

O diagrama completo está disponível em: `docs/arquitetura.drawio`

Resumo das classes por pacote:
- **core/**: FLServer, IoHTClient, ResourceProfile, ModelUpdate
- **aggregation/**: FedAvgAggregator, WeightedAggregator, RobustAggregator, MultiKrumAggregator
- **consensus/**: ThresholdConsensus, VotingConsensus, HotStuffConsensus
- **data/**: DataRepository, SyntheticHealthDataGenerator
- **runner/**: ExperimentRunner

## Arquitetura Edge-Fog-Cloud

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLOUD                                   │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   FLServer      │    │ ExperimentRunner│                     │
│  │  (Agregação +   │───▶│  (Orquestração  │                     │
│  │   Consenso)     │    │   + Export)     │                     │
│  └────────┬────────┘    └─────────────────┘                     │
│           │                                                  │
└───────────┼──────────────────────────────────────────────────────┘
            │ updates
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                           FOG                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ConsensusModule                              │   │
│  │    (Threshold / Voting / HotStuff)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │ validadas                                          │
│           ▼                                                    │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          EDGE                                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │ IoHT   │ │ IoHT   │ │ IoHT   │ │ IoHT   │ │ IoHT   │  ...   │
│  │Client 1│ │Client 2│ │Client 3│ │Client 4│ │Client n│        │
│  │  📊    │ │  📊    │ │  📊    │ │  📊    │ │  📊    │        │
│  │  train │ │  train │ │  train │ │  train │ │  train │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
│       │         │         │         │         │                 │
│       ▼         ▼         ▼         ▼         ▼                 │
│  [Dados Sintéticos de Saúde - FC, Temp, labels]                 │
└─────────────────────────────────────────────────────────────────┘
```

**Camadas:**
- **Edge**: Dispositivos IoHT (clientes) com dados locais e treinamento local
- **Fog**: Módulo de consenso que valida atualizações antes da agregação
- **Cloud**: Servidor FL que coordena rodadas, agrega modelos e exporta resultados

**Fluxo de dados (single-process):**
1. Dados sintéticos são gerados para cada cliente Edge
2. Clientes executam treinamento local e geram ModelUpdate
3. Consenso (Fog) filtra/valida atualizações
4. Agregador (Cloud) produz novo modelo global
5. Ciclo se repete por rodadas configuradas

## Implantação Docker (3 serviços)

Em ambiente Docker, cada camada é um container independente com comunicação via HTTP:

```
┌─────────────────────────────────────────────────────────────┐
│                      docker-compose.yml                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   CLOUD                               │   │
│  │  scripts/cloud_service.py                             │   │
│  │  porta: - (initiator)                                 │   │
│  │                                                       │   │
│  │  Agregador (FedAvg / Weighted / Robust / MultiKrum)   │   │
│  │  Export CSV/JSON → volume ./results                   │   │
│  └──────────────┬───────────────────────────────────────-┘   │
│                 │ POST /train                                │
│                 ▼                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    EDGE                                │   │
│  │  scripts/edge_service.py                              │   │
│  │  porta: 8000                                          │   │
│  │                                                       │   │
│  │  N IoHTClient + DataRepository (dados sintéticos)     │   │
│  │  Treinamento local e simulação de falhas              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│                 ┌─────────────────────────────────────────┐  │
│                 │          FOG                             │  │
│                 │  scripts/fog_service.py                  │  │
│                 │  porta: 8001                             │  │
│                 │                                          │  │
│                 │  ConsensusModule                         │  │
│                 │  (Threshold / Voting / HotStuff)         │  │
│                 └─────────────────────────────────────────┘  │
│                           ▲                                   │
│                 POST /validate                                │
└───────────────────────────┼──────────────────────────────────-┘
```

### Serviços

| Serviço | Script | Porta | Responsabilidade |
|---------|--------|-------|------------------|
| **edge** | `scripts/edge_service.py` | 8000 | Gerencia N clientes IoHT com dados sintéticos. `POST /train`: recebe modelo global + lista de clientes, treina localmente, retorna updates |
| **fog** | `scripts/fog_service.py` | 8001 | Executa o módulo de consenso. `POST /validate`: recebe updates + round_num, retorna subconjunto válido |
| **cloud** | `scripts/cloud_service.py` | - | Orquestrador. Seleciona clientes, chama Edge, chama Fog, agrega, exporta resultados |

### Fluxo entre serviços (Docker)

```
CLOUD                              EDGE                    FOG
  │                                 │                       │
  ├── POST /train ─────────────────►│                       │
  │   {global_model, client_ids}    │                       │
  │                                 │                       │
  │   each client:                  │                       │
  │     receive_global_model()      │                       │
  │     train_local_model()         │                       │
  │                                 │                       │
  │◄── {updates: [...]} ────────────│                       │
  │                                 │                       │
  ├── POST /validate ──────────────────────────────────────►│
  │   {updates, round_num}          │                       │
  │                                 │                       │
  │◄── {valid: [...]} ──────────────────────────────────────│
  │                                 │                       │
  │ aggregate(valid)                │                       │
  │ update global_model             │                       │
  │                                 │                       │
  └── (próxima rodada) ────────────►│                       │
```

### Execução

```bash
docker compose up --build
```

A configuração de cada camada é feita via variáveis de ambiente no `docker-compose.yml`. Consulte o arquivo para a lista completa de `CONFIG_*` disponíveis.

## Pacotes (domain-driven)

```
src/iomt_fl_consensus/
├── __init__.py          # Re-exports da API pública
├── core/                # Entidades centrais
│   ├── models.py        #   ResourceProfile, ModelUpdate
│   ├── client.py        #   IoHTClient
│   └── server.py        #   FLServer (coordena rodadas, distribui modelo)
├── aggregation/         # Estratégias de agregação
│   ├── fedavg.py        #   FedAvgAggregator
│   ├── weighted.py      #   WeightedAggregator
│   ├── robust.py        #   RobustAggregator
│   └── multi_krum.py    #   MultiKrumAggregator
├── consensus/           # Mecanismos de validação/consenso
│   ├── threshold.py     #   ThresholdConsensus
│   ├── voting.py        #   VotingConsensus
│   └── hotstuff.py      #   HotStuffConsensus
├── data/                # Geração de dados sintéticos
│   ├── generator.py     #   SyntheticHealthDataGenerator
│   └── repository.py    #   DataRepository
└── runner/              # Execução de cenários
    └── experiment.py    #   ExperimentRunner, setup_logging
```

### core
- `models.py`: `ResourceProfile` (recursos do dispositivo), `ModelUpdate` (pesos + metadados)
- `client.py`: `IoHTClient` – dispositivo virtual que treina localmente e envia atualizações
- `server.py`: `FLServer` – coordena rodadas, seleciona clientes, distribui modelo global

### aggregation
- `FedAvgAggregator`: Média aritmética simples dos pesos
- `WeightedAggregator`: Média ponderada por tamanho do dataset de cada cliente
- `RobustAggregator`: Mediana por coeficiente – rejeita outliers via desvio máximo configurável
- `MultiKrumAggregator`: Seleciona as `m` atualizações com menor soma de distâncias euclidianas entre si e calcula a média; parâmetro `f` define o número esperado de Bizantinos

### consensus
- `ThresholdConsensus`: Filtra atualizações com desvio acima de `max_deviation` em qualquer coeficiente
- `VotingConsensus`: Seleciona os coeficientes por moda entre as atualizações recebidas
- `HotStuffConsensus`: Consenso BFT baseado em comitê – requer 3f+1 validadores, quórum de 2f+1, líder eleito deterministicamente por rodada

### data
- `SyntheticHealthDataGenerator`: Gera amostras sintéticas de sinais vitais (FC, temperatura, SpO₂) com drift opcional
- `DataRepository`: Cria e gerencia datasets por cliente

### runner
- `ExperimentRunner`: Orquestra a execução do cenário, exporta métricas em CSV e JSON
- `setup_logging`: Configura nível, formato (json/text) e arquivo de log

## Fluxo de execução

### Modo single-process (local)
1. `scripts/run_demo.py` carrega a configuração (JSON ou env vars).
2. `DataRepository` cria dados sintéticos por cliente (com drift opcional se `non_iid`).
3. `FLServer` inicializa o modelo global e seleciona clientes por rodada.
4. Cada `IoHTClient` treina localmente e gera um `ModelUpdate`.
5. O módulo de consenso valida/filtra as atualizações (Threshold, Voting ou HotStuff).
6. O agregador combina as atualizações válidas em um novo modelo global (FedAvg, Weighted, Robust ou MultiKrum).
7. O ciclo (passos 3-6) se repete pelo número de rodadas configurado.
8. Métricas por rodada são exportadas em CSV e JSON.

### Modo Docker (3 containers)
1. `cloud_service.py` lê a configuração de variáveis de ambiente (`CONFIG_*`).
2. `edge_service.py` gera N clientes com dados sintéticos no startup e aguarda requisições.
3. `fog_service.py` instancia o módulo de consenso e aguarda requisições.
4. A cada rodada, o `cloud` chama `POST /train` no `edge` com o modelo global e os IDs dos clientes selecionados.
5. O `edge` treina cada cliente localmente e retorna os `ModelUpdate` serializados em JSON.
6. O `cloud` chama `POST /validate` no `fog` com os updates coletados.
7. O `fog` valida e retorna apenas os updates aprovados.
8. O `cloud` agrega os updates válidos e atualiza o modelo global.
9. O ciclo (passos 4-8) se repete pelo número de rodadas configurado.
10. Ao final, o `cloud` exporta CSV e JSON no volume compartilhado `./results`.

## Configuração (JSON)
```json
{
  "num_clients": 20,
  "rounds": 10,
  "client_fraction": 0.5,
  "aggregator": "fedavg",
  "consensus": "threshold",
  "max_deviation": 0.3,
  "failure_rate": 0.0,
  "noise": 0.0,
  "non_iid": false
}
```

Campos específicos para agregadores/consensos avançados:
- **multi_krum**: `f` (nº esperado de Bizantinos, default 1)
- **hotstuff**: `f` (tolerância a falhas, default 1)

## Extensibilidade
- **Novo agregador**: criar classe em `src/iomt_fl_consensus/aggregation/` seguindo a interface `aggregate(updates) -> Dict[str, float]` e registrar em `runner/experiment.py:_build_aggregator()`. No modo Docker, o cloud importa o agregador diretamente.
- **Novo consenso**: criar classe em `src/iomt_fl_consensus/consensus/` seguindo a interface `validate_updates(updates, round_num=1) -> List[ModelUpdate]` e registrar em `scripts/fog_service.py:_build_consensus()`. No modo local, registrar em `runner/experiment.py:_build_consensus()`.
- **Novo cenário**: adicionar arquivo JSON em `config/` (modo local) ou definir `CONFIG_*` no `docker-compose.yml` (modo Docker).
