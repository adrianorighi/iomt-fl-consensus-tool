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

**Fluxo de dados:**
1. Dados sintéticos são gerados para cada cliente Edge
2. Clientes executam treinamento local e geram ModelUpdate
3. Consenso (Fog) filtra/valida atualizações
4. Agregador (Cloud) produz novo modelo global
5. Ciclo se repete por rodadas configuradas

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
1. O `ExperimentRunner` carrega a configuração JSON.
2. O `DataRepository` cria dados sintéticos por cliente (com drift opcional se `non_iid`).
3. O `FLServer` inicializa o modelo global e seleciona clientes por rodada.
4. Cada `IoHTClient` treina localmente e gera um `ModelUpdate`.
5. O módulo de consenso valida/filtra as atualizações (Threshold, Voting ou HotStuff).
6. O agregador combina as atualizações válidas em um novo modelo global (FedAvg, Weighted, Robust ou MultiKrum).
7. O ciclo (passos 3-6) se repete pelo número de rodadas configurado.
8. Métricas por rodada são exportadas em CSV e JSON.

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
- **Novo agregador**: criar classe em `src/iomt_fl_consensus/aggregation/` seguindo a interface `aggregate(updates) -> Dict[str, float]` e registrar em `runner/experiment.py:_build_aggregator()`
- **Novo consenso**: criar classe em `src/iomt_fl_consensus/consensus/` seguindo a interface `validate_updates(updates, round_num=1) -> List[ModelUpdate]` e registrar em `runner/experiment.py:_build_consensus()`
- **Novo cenário**: adicionar arquivo JSON em `config/`
