# AGENTS.md - IoMT-FL Consensus Tool

## Execução
python scripts/run_demo.py --config config/scenario_baseline.json
python tests/test_smoke.py

## Cenários
- scenario_baseline.json - FedAvg + Threshold, dados IID
- scenario_non_iid.json - Weighted + Voting, não-IID
- scenario_robust.json - Robust + Threshold, com falhas

## Arquitetura (latex/main.tex)
- FLServer: coordena rodadas FL
- IoHTClient: dispositivo virtual
- Aggregators: FedAvg, Weighted, Robust
- Consensus: Threshold, Voting
- DataRepository: dados sintéticos
- ExperimentRunner: execução e exportação

## Config JSON
num_clients, rounds, client_fraction, aggregator, consensus, max_deviation, failure_rate, noise, non_iid

## Extensibilidade
Adicionar agregador: src/iomt_fl_consensus/aggregation/ + runner/experiment.py
Adicionar consenso: src/iomt_fl_consensus/consensus/ + runner/experiment.py

## Saídas
results/*.csv, results/*.json (métricas por rodada)